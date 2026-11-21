//! Writes the JSON Schema of `scene.json` to stdout or to the given path.
//! Used to generate TypeScript and Pydantic types.

fn main() -> std::io::Result<()> {
    let schema = serde_json::to_string_pretty(&scene_schema::scene_json_schema())?;
    match std::env::args().nth(1) {
        Some(path) => std::fs::write(path, schema + "\n"),
        None => {
            println!("{schema}");
            Ok(())
        }
    }
}
