//! Minimal binary glTF (GLB 2.0) writer for textured meshes.
//!
//! Written by hand instead of pulling a glTF serialization library: the subset needed
//! here (a few named meshes, each with an optional texture) is small, and it keeps the
//! output fully under our control. Materials use `KHR_materials_unlit` so photo textures
//! are shown as-is, without being re-lit by the viewer.

use serde_json::{Value, json};

use crate::GeomError;
use crate::mesh::Mesh;

/// An encoded image (PNG or JPEG bytes) used as a mesh's base color texture.
#[derive(Debug, Clone, Copy)]
pub struct Texture<'a> {
    pub bytes: &'a [u8],
    /// `image/png` or `image/jpeg`.
    pub mime_type: &'a str,
}

/// One named node of a multi-mesh GLB (e.g. one object layer, or the background).
#[derive(Debug, Clone, Copy)]
pub struct GlbPart<'a> {
    pub name: &'a str,
    pub mesh: &'a Mesh,
    pub texture: Option<Texture<'a>>,
}

const GLB_MAGIC: u32 = 0x4654_6C67; // "glTF"
const CHUNK_JSON: u32 = 0x4E4F_534A; // "JSON"
const CHUNK_BIN: u32 = 0x004E_4942; // "BIN\0"
const ARRAY_BUFFER: u32 = 34962;
const ELEMENT_ARRAY_BUFFER: u32 = 34963;
const FLOAT: u32 = 5126;
const UNSIGNED_INT: u32 = 5125;

/// Serializes a single mesh (and optional texture) to a `.glb` file in memory.
pub fn write_glb(mesh: &Mesh, texture: Option<Texture<'_>>) -> Result<Vec<u8>, GeomError> {
    write_glb_scene(&[GlbPart {
        name: "mesh",
        mesh,
        texture,
    }])
}

/// Serializes several named meshes, each with its own material and optional texture,
/// as sibling nodes of one scene.
pub fn write_glb_scene(parts: &[GlbPart<'_>]) -> Result<Vec<u8>, GeomError> {
    let mut bin = Vec::new();
    let mut views: Vec<Value> = Vec::new();
    let mut accessors = Vec::new();
    let mut nodes = Vec::new();
    let mut meshes = Vec::new();
    let mut materials = Vec::new();
    let mut images = Vec::new();
    let mut textures = Vec::new();

    let mut push_view = |bin: &mut Vec<u8>, bytes: &[u8], target: Option<u32>| {
        pad_to_4(bin, 0);
        let mut view = json!({ "buffer": 0, "byteOffset": bin.len(), "byteLength": bytes.len() });
        if let Some(t) = target {
            view["target"] = json!(t);
        }
        bin.extend_from_slice(bytes);
        views.push(view);
        views.len() - 1
    };

    for part in parts {
        let mesh = part.mesh;
        if mesh.positions.len() > u32::MAX as usize {
            return Err(GeomError::TooManyVertices(mesh.positions.len()));
        }
        let pos_bytes: Vec<u8> = mesh
            .positions
            .iter()
            .flat_map(|p| p.to_array())
            .flat_map(f32::to_le_bytes)
            .collect();
        let uv_bytes: Vec<u8> = mesh
            .uvs
            .iter()
            .flat_map(|uv| uv.to_array())
            .flat_map(f32::to_le_bytes)
            .collect();
        let idx_bytes: Vec<u8> = mesh.indices.iter().flat_map(|i| i.to_le_bytes()).collect();

        let pos_view = push_view(&mut bin, &pos_bytes, Some(ARRAY_BUFFER));
        let uv_view = push_view(&mut bin, &uv_bytes, Some(ARRAY_BUFFER));
        let idx_view = push_view(&mut bin, &idx_bytes, Some(ELEMENT_ARRAY_BUFFER));

        let (min, max) = mesh
            .bounds()
            .map(|(lo, hi)| (lo.to_array(), hi.to_array()))
            .unwrap_or(([0.0; 3], [0.0; 3]));
        let a = accessors.len();
        accessors.push(json!({ "bufferView": pos_view, "componentType": FLOAT,
            "count": mesh.positions.len(), "type": "VEC3", "min": min, "max": max }));
        accessors.push(json!({ "bufferView": uv_view, "componentType": FLOAT,
            "count": mesh.uvs.len(), "type": "VEC2" }));
        accessors.push(
            json!({ "bufferView": idx_view, "componentType": UNSIGNED_INT,
            "count": mesh.indices.len(), "type": "SCALAR" }),
        );

        let mut material = json!({
            "name": part.name,
            "pbrMetallicRoughness": { "metallicFactor": 0.0, "roughnessFactor": 1.0 },
            "doubleSided": true,
            "extensions": { "KHR_materials_unlit": {} }
        });
        match part.texture {
            Some(t) => {
                let img_view = push_view(&mut bin, t.bytes, None);
                images.push(json!({ "bufferView": img_view, "mimeType": t.mime_type }));
                textures.push(json!({ "source": images.len() - 1, "sampler": 0 }));
                material["pbrMetallicRoughness"]["baseColorTexture"] =
                    json!({ "index": textures.len() - 1 });
            }
            None => {
                material["pbrMetallicRoughness"]["baseColorFactor"] = json!([0.8, 0.8, 0.8, 1.0]);
            }
        }
        materials.push(material);
        meshes.push(json!({ "name": part.name, "primitives": [{
            "attributes": { "POSITION": a, "TEXCOORD_0": a + 1 },
            "indices": a + 2,
            "material": materials.len() - 1
        }]}));
        nodes.push(json!({ "name": part.name, "mesh": meshes.len() - 1 }));
    }
    pad_to_4(&mut bin, 0);

    let mut doc = json!({
        "asset": { "version": "2.0", "generator": "3Dworld geom-core" },
        "extensionsUsed": ["KHR_materials_unlit"],
        "scene": 0,
        "scenes": [{ "nodes": (0..nodes.len()).collect::<Vec<_>>() }],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{ "byteLength": bin.len() }]
    });
    if !images.is_empty() {
        doc["images"] = Value::Array(images);
        doc["textures"] = Value::Array(textures);
        doc["samplers"] = json!([{ "magFilter": 9729, "minFilter": 9987 }]);
    }

    let mut json_bytes = serde_json::to_vec(&doc).expect("glTF JSON serializes");
    pad_to_4(&mut json_bytes, b' ');

    let total = 12 + 8 + json_bytes.len() + 8 + bin.len();
    let mut out = Vec::with_capacity(total);
    out.extend_from_slice(&GLB_MAGIC.to_le_bytes());
    out.extend_from_slice(&2u32.to_le_bytes());
    out.extend_from_slice(&(total as u32).to_le_bytes());
    out.extend_from_slice(&(json_bytes.len() as u32).to_le_bytes());
    out.extend_from_slice(&CHUNK_JSON.to_le_bytes());
    out.extend_from_slice(&json_bytes);
    out.extend_from_slice(&(bin.len() as u32).to_le_bytes());
    out.extend_from_slice(&CHUNK_BIN.to_le_bytes());
    out.extend_from_slice(&bin);
    Ok(out)
}

fn pad_to_4(buf: &mut Vec<u8>, fill: u8) {
    while !buf.len().is_multiple_of(4) {
        buf.push(fill);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{GridMeshOptions, PointMap, grid_mesh};
    use scene_schema::Intrinsics;

    // 1x1 red PNG.
    const PNG: &[u8] = &[
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44,
        0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90,
        0x77, 0x53, 0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8,
        0xCF, 0xC0, 0x00, 0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB0, 0x00, 0x00, 0x00,
        0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ];

    fn sample_mesh() -> Mesh {
        let k = Intrinsics::from_fov_x(1.0, 5, 4);
        let pm = PointMap::from_depth(&[2.0; 20], &k).unwrap();
        grid_mesh(&pm, &GridMeshOptions::default()).unwrap()
    }

    #[test]
    fn textured_glb_is_readable_by_gltf_crate() {
        let mesh = sample_mesh();
        let glb = write_glb(
            &mesh,
            Some(Texture {
                bytes: PNG,
                mime_type: "image/png",
            }),
        )
        .unwrap();
        assert_eq!(glb.len() % 4, 0);
        let (doc, buffers, images) = gltf::import_slice(&glb).expect("valid GLB");
        assert_eq!(images.len(), 1);
        let prim = doc.meshes().next().unwrap().primitives().next().unwrap();
        let reader = prim.reader(|b| Some(&buffers[b.index()]));
        let positions: Vec<[f32; 3]> = reader.read_positions().unwrap().collect();
        let indices: Vec<u32> = reader.read_indices().unwrap().into_u32().collect();
        assert_eq!(positions.len(), mesh.positions.len());
        assert_eq!(indices, mesh.indices);
        assert_eq!(positions[0], mesh.positions[0].to_array());
    }

    #[test]
    fn multi_part_scene_keeps_names_and_textures() {
        let a = sample_mesh();
        let b = Mesh::default();
        let tex = Texture {
            bytes: PNG,
            mime_type: "image/png",
        };
        let glb = write_glb_scene(&[
            GlbPart {
                name: "background",
                mesh: &a,
                texture: Some(tex),
            },
            GlbPart {
                name: "obj-1",
                mesh: &a,
                texture: Some(tex),
            },
            GlbPart {
                name: "empty",
                mesh: &b,
                texture: None,
            },
        ])
        .unwrap();
        let (doc, _, images) = gltf::import_slice(&glb).expect("valid GLB");
        let names: Vec<_> = doc.nodes().map(|n| n.name().unwrap().to_owned()).collect();
        assert_eq!(names, ["background", "obj-1", "empty"]);
        assert_eq!(images.len(), 2);
        assert_eq!(doc.scenes().next().unwrap().nodes().count(), 3);
    }

    #[test]
    fn untextured_and_empty_meshes_are_valid() {
        let glb = write_glb(&sample_mesh(), None).unwrap();
        gltf::Gltf::from_slice(&glb).expect("valid untextured GLB");
        let empty = write_glb(&Mesh::default(), None).unwrap();
        gltf::Gltf::from_slice(&empty).expect("valid empty GLB");
    }
}
