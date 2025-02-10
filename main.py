# this must be the first import
import src.config as config
config.SKIP_AI = False  # it's default if starting main, False = default for tests etc.
config.read_configuration()

from src.UI import create_gradio_interface
import src.analytics as analytics
import src.utils as utils
import gradio as gr


if __name__ == "__main__":
    app = None
    try:
        # if config.read_configuration() == None:
        #     print("read configuration failed")

        if config.SKIP_AI:
            print("ai is deactivated")
        else:
            print("initializing ai models")
            model = config.get_model()
            if model.endswith("safetensors"):
                utils.download_file_if_not_existing(url=config.get_model_url(), local_path=model)

            try:
                utils.download_file_if_not_existing(config.get_modelurl_onnx_age_googlenet(), local_path=config.get_modelfile_onnx_age_googlenet())
                utils.download_file_if_not_existing(config.get_modelurl_onnx_gender_googlenet(), local_path=config.get_modelfile_onnx_gender_googlenet())
            except Exception as e:
                print("could not detect or download face recognition models", e)


        if config.is_analytics_enabled():
            analytics.start()
        title = config.get_app_title()
        print("starting Server with title:", title)
        app = create_gradio_interface()
        app.launch(
            server_name="0.0.0.0",#TODO: add ip to config
            server_port=config.get_server_port(),
            share=config.is_gradio_shared(),
            show_error=config.DEBUG,
            show_api=False,
            enable_monitoring=False,
            max_file_size=12*gr.FileSize.MB
        )
        analytics.stop()
    except Exception as e:
        print(e)
    finally:
        if app != None:
            app.close()
        print("app closed")
