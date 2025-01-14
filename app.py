import argparse
import logging
from typing import Union

# mostly likely you'll need these modules/classes
from clams import ClamsApp, Restifier
from mmif import Mmif, View, Document, AnnotationTypes, DocumentTypes
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
        input_view = mmif.get_views_for_document(video_doc.properties.id)[-1]
        new_view: View = mmif.new_view()
        self.sign_view(new_view, parameters)

        for timeframe in input_view.get_annotations(AnnotationTypes.TimeFrame):
            self.logger.debug(timeframe.properties)
            representatives = timeframe.get("representatives") if "representatives" in timeframe.properties else None
            if representatives:
                frame_number = vdh.get_representative_framenum(mmif, timeframe)
                image = vdh.extract_representative_frame(mmif, timeframe, as_PIL=True)
            else:
                frame_number = vdh.get_mid_framenum(mmif, timeframe)
                image = vdh.extract_mid_frame(mmif, timeframe, as_PIL=True)

            self.logger.debug("Extracted image")
            self.logger.debug("Running OCR")
            ocrs = [self.reader.readtext(np.array(image), width_ths=0.25)]
            self.logger.debug(ocrs)
            timepoint = new_view.new_annotation(AnnotationTypes.TimePoint)
            timepoint.add_property('timePoint', frame_number)
            point_frame = new_view.new_annotation(AnnotationTypes.Alignment)
            point_frame.add_property("source", timeframe.long_id)
            point_frame.add_property("target", timepoint.id)
            for ocr in ocrs:
                for coord, text, score in ocr:
                    if score > 0.4:
                        self.logger.debug("Confident OCR: " + text)
                        text_document = new_view.new_textdocument(text)
                        bbox_annotation = new_view.new_annotation(AnnotationTypes.BoundingBox)
                        bbox_annotation.add_property("coordinates", coord)
                        bbox_annotation.add_property("boxType", "text")
                        time_bbox = new_view.new_annotation(AnnotationTypes.Alignment)
                        time_bbox.add_property("source", timepoint.id)
                        time_bbox.add_property("target", bbox_annotation.id)
                        bbox_text = new_view.new_annotation(AnnotationTypes.Alignment)
                        bbox_text.add_property("source", bbox_annotation.id)
                        bbox_text.add_property("target", text_document.id)

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
