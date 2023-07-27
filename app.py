import argparse
import logging
from typing import Union, List, Dict, Tuple, Iterable

# mostly likely you'll need these modules/classes
from clams import ClamsApp, Restifier
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes
from mmif.utils import video_document_helper as vdh

import easyocr
import torch
import numpy as np


class EasyOcrWrapper(ClamsApp):

    def __init__(self):
        super().__init__()
        gpu = True if torch.cuda.is_available() else False
        self.reader = easyocr.Reader(['en'], gpu=gpu)

    def _appmetadata(self):
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._load_appmetadata
        # Also check out ``metadata.py`` in this directory.
        # When using the ``metadata.py`` leave this do-nothing "pass" method here.
        pass

    def _annotate(self, mmif: Union[str, dict, Mmif], **parameters) -> Mmif:
        self.logger.debug("running app")
        video_doc: Document = mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0]
        input_view: View = mmif.get_views_for_document(video_doc.properties.id)[0]

        config = self.get_configuration(**parameters)
        new_view: View = mmif.new_view()
        self.sign_view(new_view, parameters)
        new_view.new_contain(
            AnnotationTypes.Relation,
            document=video_doc.id,
        )

        for timeframe in input_view.get_annotations(AnnotationTypes.TimeFrame):
            self.logger.debug(timeframe.properties)
            # get images from time frame
            if config["sampleFrames"] == 1:
                image: np.ndarray = vdh.extract_mid_frame(mmif, timeframe, as_PIL=False)
                ocrs = [self.reader.readtext(image)]
                self.logger.debug(ocrs)
            else:
                self.logger.debug(f"Sampling {config['sampleFrames']} frames")
                timeframe_length = int(timeframe.properties["end"] - timeframe.properties["start"])
                sample_frames = config["sampleFrames"]
                if timeframe_length < sample_frames:
                    sample_frames = int(timeframe_length)
                sample_ratio = int(timeframe.properties["end"]
                                   - timeframe.properties["start"]) // sample_frames
                tf_sample = vdh.sample_frames(timeframe.properties["start"], timeframe.properties["end"],
                                              sample_ratio)
                images = vdh.extract_frames_as_images(video_doc, tf_sample)
                ocrs = []
                for image in images:
                    ocrs.append(self.reader.readtext(image))

            full_text = ""
            scores = []
            for ocr in ocrs:
                for coord, text, score in ocr:
                    if score > 0.4:
                        full_text += text + " "
                        scores.append(score)

            self.logger.debug("Confident OCR: " + full_text)

            # add OCR output to text document
            text_document = new_view.new_textdocument(full_text)
            # text_document.add_property("confidence", score)
            align_annotation = new_view.new_annotation(AnnotationTypes.Alignment)
            align_annotation.add_property("source", timeframe.id)
            align_annotation.add_property("target", text_document.id)
            pass

        return mmif


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", default="5000", help="set port to listen")
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # add more arguments as needed
    # parser.add_argument(more_arg...)

    parsed_args = parser.parse_args()

    # create the app instance
    app = EasyOcrWrapper()

    http_app = Restifier(app, port=int(parsed_args.port))
    # for running the application in production mode
    if parsed_args.production:
        http_app.serve_production()
    # development mode
    else:
        app.logger.setLevel(logging.DEBUG)
        http_app.run()
