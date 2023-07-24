import argparse
from typing import Union, List, Dict, Tuple, Iterable

# mostly likely you'll need these modules/classes
from clams import ClamsApp, Restifier
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes
from mmif.utils import video_document_helper as vdh

import torch
from transformers import Pix2StructForConditionalGeneration as psg
from transformers import Pix2StructProcessor as psp


class EasyOcrWrapper(ClamsApp):

    def __init__(self):
        super().__init__()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = psg.from_pretrained("google/pix2struct-docvqa-base").to(self.device)
        self.processor = psp.from_pretrained("google/pix2struct-docvqa-base")

    def _appmetadata(self):
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._load_appmetadata
        # Also check out ``metadata.py`` in this directory.
        # When using the ``metadata.py`` leave this do-nothing "pass" method here.
        pass

    @staticmethod
    def vote(candidates: List[Iterable[Tuple[str, str]]]) -> Tuple[str, str]:
        """
        For each question, vote on the most common answer
        :param candidates: completion candidates
        :return: query and the most common answer
        """
        answers = []
        query: str = ""
        for candidate in candidates:
            for query, answer in candidate:
                query = query
                answers.append(answer)
        return query, max(set(answers), key=answers.count)

    def generate(self, img, questions):
        inputs = self.processor(images=[img for _ in range(len(questions))],
                                text=questions, return_tensors="pt").to(self.device)
        predictions = self.model.generate(**inputs, max_new_tokens=256)
        return zip(questions, self.processor.batch_decode(predictions, skip_special_tokens=True))

    def _annotate(self, mmif: Union[str, dict, Mmif], **parameters) -> Mmif:
        video_doc: Document = mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0]
        input_view: View = mmif.get_views_for_document(video_doc.properties.id)[0]

        config = self.get_configuration(**parameters)
        new_view: View = mmif.new_view()
        self.sign_view(new_view, parameters)
        new_view.new_contain(
            AnnotationTypes.Relation,
            document=video_doc.id,
        )

        input_queries = parameters.get("query")
        input_queries = [query.replace('+', ' ') for query in input_queries]

        query_to_label = {}
        queries = []

        for item in input_queries:
            query, label = item.split('@')
            query_to_label[query] = label
            queries.append(query)

        for timeframe in input_view.get_annotations(AnnotationTypes.TimeFrame, label=config["frameType"]):
            print(timeframe.properties)
            # get images from time frame
            if config["sampleFrames"] == 1:
                image = vdh.extract_mid_frame(mmif, timeframe, as_PIL=True)
                completions = self.generate(image, queries)
            else:
                timeframe_length = int(timeframe.properties["end"] - timeframe.properties["start"])
                sample_frames = config["sampleFrames"]
                if timeframe_length < sample_frames:
                    sample_frames = int(timeframe_length)
                sample_ratio = int(timeframe.properties["start"]
                                   + timeframe.properties["end"]) // sample_frames
                tf_sample = vdh.sample_frames(timeframe.properties["start"], timeframe.properties["end"],
                                              sample_ratio)
                images = vdh.extract_frames_as_images(video_doc, tf_sample)
                completions = []
                for query in queries:
                    candidates = []
                    for image in images:
                        candidates.append(self.generate(image, query))
                    completions.append(self.vote(candidates))

            for query, answer in completions:
                print(f"query: {query} answer: {answer}")
            # add question answer pairs as properties to timeframe
                text_document = new_view.new_textdocument(answer)
                text_document.add_property("query", query)
                text_document.add_property("label", query_to_label[query])
                align_annotation = new_view.new_annotation(AnnotationTypes.Alignment)
                align_annotation.add_property("source", timeframe.id)
                align_annotation.add_property("target", text_document.id)
            pass

        return mmif


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", action="store", default="5000", help="set port to listen"
    )
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # more arguments as needed
    # parser.add_argument(more_arg...)

    parsed_args = parser.parse_args()

    # create the app instance
    app = EasyOcrWrapper()

    http_app = Restifier(app, port=int(parsed_args.port))

    if parsed_args.production:
        http_app.serve_production()
    else:
        http_app.run()
