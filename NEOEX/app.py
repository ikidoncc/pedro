"""Entry point for NEOEX — EXPONENCIAL LAB."""
from neoex.ui import build_app, CSS, MATHJAX_HEAD, MATHJAX_ASSET_DIR
import gradio as gr

app = build_app()

if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        css=CSS,
        head=MATHJAX_HEAD,
        allowed_paths=[str(MATHJAX_ASSET_DIR)],
        theme=gr.themes.Base(primary_hue="cyan", secondary_hue="purple", neutral_hue="slate"),
    )
