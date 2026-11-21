//! Per-object review state machine (PLAN.md §1.1–1.2).
//!
//! An object moves forward one stage at a time, each step approved by the user:
//!
//! ```text
//! Proposed → LabelConfirmed → Completed → CompletionApproved → Generating3d → Ready3d → Placed
//! ```
//!
//! When an upstream input changes (label, mask, completion), downstream outputs are
//! **not** deleted or regenerated automatically: they are marked `stale` and the user
//! decides whether to spend credits to refresh them. Generation failures are recorded
//! in `failure` and can be retried.

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize, JsonSchema,
)]
#[serde(rename_all = "snake_case")]
pub enum Stage {
    /// Detected by the model, waiting for the user.
    Proposed,
    /// Label and mask approved or corrected by the user.
    LabelConfirmed,
    /// Amodal completion generated, waiting for approval.
    Completed,
    /// Completion approved by the user.
    CompletionApproved,
    /// 3D generation running.
    Generating3d,
    /// 3D asset generated.
    Ready3d,
    /// Asset aligned into the scene.
    Placed,
}

impl Stage {
    pub fn next(self) -> Option<Stage> {
        use Stage::*;
        Some(match self {
            Proposed => LabelConfirmed,
            LabelConfirmed => Completed,
            Completed => CompletionApproved,
            CompletionApproved => Generating3d,
            Generating3d => Ready3d,
            Ready3d => Placed,
            Placed => return None,
        })
    }
}

/// An upstream edit made by the user.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum Change {
    Label,
    Mask,
    /// A different completion candidate was chosen or regenerated.
    Completion,
}

impl Change {
    /// First stage whose outputs become outdated because of this change.
    pub fn invalidates_from(self) -> Stage {
        match self {
            Change::Label | Change::Mask => Stage::Completed,
            Change::Completion => Stage::Ready3d,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct ObjectStatus {
    pub stage: Stage,
    /// Outputs at or after `stale_from` exist but no longer match their inputs.
    pub stale_from: Option<Stage>,
    /// Last generation error, if the most recent attempt failed.
    pub failure: Option<String>,
}

impl Default for ObjectStatus {
    fn default() -> Self {
        Self {
            stage: Stage::Proposed,
            stale_from: None,
            failure: None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum StatusError {
    #[error("cannot go from {from:?} to {to:?}; stages advance one at a time")]
    InvalidTransition { from: Stage, to: Stage },
    #[error("outputs from {0:?} on are stale; regenerate them before advancing")]
    Stale(Stage),
    #[error("only a running 3D generation can fail")]
    NotGenerating,
}

impl ObjectStatus {
    pub fn is_stale(&self) -> bool {
        self.stale_from.is_some()
    }

    /// Advances exactly one stage. Refused while a stale output would be built upon.
    pub fn advance(&mut self, to: Stage) -> Result<(), StatusError> {
        if self.stage.next() != Some(to) {
            return Err(StatusError::InvalidTransition {
                from: self.stage,
                to,
            });
        }
        if let Some(s) = self.stale_from
            && s <= self.stage
        {
            return Err(StatusError::Stale(s));
        }
        self.stage = to;
        self.failure = None;
        Ok(())
    }

    /// Records a user edit. Downstream outputs that already exist become stale;
    /// nothing is regenerated automatically.
    pub fn apply_change(&mut self, change: Change) {
        let from = change.invalidates_from();
        if self.stage >= from {
            self.stale_from = Some(self.stale_from.map_or(from, |s| s.min(from)));
        }
    }

    /// Called when the user chose to regenerate stale outputs: the object goes back to
    /// the last stage that is still valid, and will advance again from there.
    pub fn rewind_for_regeneration(&mut self) {
        if let Some(from) = self.stale_from.take() {
            // `from` is never `Proposed`, so the previous stage always exists.
            self.stage = match from {
                Stage::Completed => Stage::LabelConfirmed,
                Stage::Ready3d => Stage::CompletionApproved,
                other => other,
            }
            .min(self.stage);
        }
    }

    /// Records a failed 3D generation. The object returns to `CompletionApproved` so it
    /// can be retried or replaced by a 2.5D card.
    pub fn fail(&mut self, reason: impl Into<String>) -> Result<(), StatusError> {
        if self.stage != Stage::Generating3d {
            return Err(StatusError::NotGenerating);
        }
        self.stage = Stage::CompletionApproved;
        self.failure = Some(reason.into());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn at(stage: Stage) -> ObjectStatus {
        ObjectStatus {
            stage,
            ..Default::default()
        }
    }

    #[test]
    fn advances_one_stage_at_a_time() {
        let mut s = ObjectStatus::default();
        assert!(s.advance(Stage::Completed).is_err());
        s.advance(Stage::LabelConfirmed).unwrap();
        s.advance(Stage::Completed).unwrap();
        assert_eq!(s.stage, Stage::Completed);
    }

    #[test]
    fn relabel_after_3d_marks_completion_and_3d_stale() {
        let mut s = at(Stage::Placed);
        s.apply_change(Change::Label);
        assert_eq!(s.stale_from, Some(Stage::Completed));
        // Stage is unchanged: outputs are kept for display, nothing is auto-regenerated.
        assert_eq!(s.stage, Stage::Placed);
    }

    #[test]
    fn relabel_before_completion_has_no_effect() {
        let mut s = at(Stage::LabelConfirmed);
        s.apply_change(Change::Label);
        assert!(!s.is_stale());
    }

    #[test]
    fn new_completion_only_invalidates_3d() {
        let mut s = at(Stage::Ready3d);
        s.apply_change(Change::Completion);
        assert_eq!(s.stale_from, Some(Stage::Ready3d));
        s.rewind_for_regeneration();
        assert_eq!(s.stage, Stage::CompletionApproved);
        assert!(!s.is_stale());
    }

    #[test]
    fn earliest_invalidation_wins() {
        let mut s = at(Stage::Placed);
        s.apply_change(Change::Completion);
        s.apply_change(Change::Mask);
        assert_eq!(s.stale_from, Some(Stage::Completed));
        s.rewind_for_regeneration();
        assert_eq!(s.stage, Stage::LabelConfirmed);
    }

    #[test]
    fn cannot_build_on_stale_output() {
        let mut s = at(Stage::Completed);
        s.apply_change(Change::Mask);
        assert_eq!(
            s.advance(Stage::CompletionApproved),
            Err(StatusError::Stale(Stage::Completed))
        );
    }

    #[test]
    fn failure_returns_to_retryable_stage() {
        let mut s = at(Stage::Generating3d);
        s.fail("out of memory").unwrap();
        assert_eq!(s.stage, Stage::CompletionApproved);
        assert_eq!(s.failure.as_deref(), Some("out of memory"));
        s.advance(Stage::Generating3d).unwrap();
        assert!(s.failure.is_none());
    }

    #[test]
    fn only_generation_can_fail() {
        assert_eq!(
            at(Stage::Proposed).fail("x"),
            Err(StatusError::NotGenerating)
        );
    }
}
