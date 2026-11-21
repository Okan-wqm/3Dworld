//! Rough timing of the depth → mesh → GLB path on a synthetic 1920x1080 frame.
//!
//! cargo run --release -p geom-core --example bench

use std::time::Instant;

use geom_core::{GridMeshOptions, PointMap, grid_mesh, write_glb};
use scene_schema::Intrinsics;

fn main() {
    let (w, h) = (1920u32, 1080u32);
    let k = Intrinsics::from_fov_x(60f32.to_radians(), w, h);
    // A sloped floor with a box in the middle: exercises the discontinuity cut.
    let depth: Vec<f32> = (0..w * h)
        .map(|i| {
            let (x, y) = (i % w, i / w);
            let floor = 2.0 + 6.0 * (1.0 - y as f32 / h as f32);
            if (800..1100).contains(&x) && (400..800).contains(&y) {
                floor * 0.6
            } else {
                floor
            }
        })
        .collect();

    let runs = 10;
    let t = Instant::now();
    let mut tris = 0;
    let mut bytes = 0;
    for _ in 0..runs {
        let pm = PointMap::from_depth(&depth, &k).unwrap();
        let mesh = grid_mesh(&pm, &GridMeshOptions::default()).unwrap();
        tris = mesh.triangle_count();
        bytes = write_glb(&mesh, None).unwrap().len();
    }
    let ms = t.elapsed().as_secs_f64() * 1000.0 / runs as f64;
    println!(
        "{w}x{h}: {ms:.1} ms per frame (point map + mesh + GLB), {tris} triangles, {:.1} MB GLB, {} threads",
        bytes as f64 / 1e6,
        rayon_threads()
    );
}

#[cfg(feature = "parallel")]
fn rayon_threads() -> usize {
    std::thread::available_parallelism().map_or(1, |n| n.get())
}
#[cfg(not(feature = "parallel"))]
fn rayon_threads() -> usize {
    1
}
