from src.UI import create_gradio_interface
import src.analytics as analytics
import src.utils as utils
import gradio as gr

import src.config as config
config.SKIP_AI = False  # it's default if starting main, False = default for tests etc.


if __name__ == "__main__":
    app = None
    try:
        if config.read_configuration() == None:
            print("read configuration failed")
        model = config.get_model()
        if model.endswith("safetensors"):
            utils.download_file_if_not_existing(url=config.get_model_url(), local_path=model)

        if config.SKIP_AI:
            print("ai is deactivated")
        else:
            print("initializing ai models")

        if config.is_analytics_enabled():
            analytics.start()
        title = config.get_app_title()
        print(f"starting Server ""{title}""")
        app = create_gradio_interface()
        app.launch(
            server_name="0.0.0.0",
            server_port=config.get_server_port(),
            share=config.is_gradio_shared(),
            max_file_size=8*gr.FileSize.MB
        )
        analytics.stop()
    except Exception as e:
        print(e)
    finally:
        if app != None:
            app.close()
        print("app closed")
