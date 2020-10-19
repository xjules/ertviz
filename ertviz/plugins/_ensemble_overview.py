import dash_html_components as html
from webviz_config import WebvizPluginABC
from ertviz.data_loader import get_ensembles
import dash_core_components as dcc


class EnsembleOverview(WebvizPluginABC):
    def __init__(self, app):
        super().__init__()

    @property
    def layout(self):
        return html.Div(
            [
                html.Div(
                    [
                        self.ensemble_view(ensemble)
                        for index, ensemble in enumerate(get_ensembles())
                    ]
                )
            ]
        )

    def ensemble_view(self, ensemble_dict):
        ensemble_id = ensemble_dict["ref_url"].split("/")[-1]
        return html.Div(
            children=[
                dcc.Link(
                    ensemble_dict["name"],
                    href="/ensemble-viewer/?ensemble_id={}".format(ensemble_id),
                ),
            ]
        )
