import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from ertviz.data_loader import get_ensemble_url
from ertviz.ert_client import get_response
from ertviz.models import EnsemblePlotModel, PlotModel, EnsembleModel
from ertviz.controllers import parse_url_query


def _get_realizations_data(realizations, x_axis):
    realizations_data = list()
    for realization in realizations:
        plot = PlotModel(
            x_axis=x_axis,
            y_axis=realization.data,
            text=realization.name,
            name=realization.name,
            line=dict(color="royalblue"),
            mode="lines+markers",
            marker=dict(color="royalblue", size=1),
        )
        realizations_data.append(plot)
    return realizations_data


def _get_observation_data(observation, x_axis):
    data = observation.values
    stds = observation.std
    x_axis_indexes = observation.data_indexes_as_axis
    x_axis = [x_axis[i] for i in x_axis_indexes]
    observation_data = PlotModel(
        x_axis=x_axis,
        y_axis=data,
        text="Observations",
        name="Observations",
        mode="markers",
        line=None,
        marker=dict(color="red", size=10),
    )
    lower_std_data = PlotModel(
        x_axis=x_axis,
        y_axis=[d - std for d, std in zip(data, stds)],
        text="Observations std lower",
        name="Observations std lower",
        mode="line",
        line=dict(color="red", dash="dash"),
        marker=None,
    )
    upper_std_data = PlotModel(
        x_axis=x_axis,
        y_axis=[d + std for d, std in zip(data, stds)],
        text="Observations std upper",
        name="Observations std upper",
        mode="line",
        line=dict(color="red", dash="dash"),
        marker=None,
    )
    return [observation_data, lower_std_data, upper_std_data]


def _create_response_model(response):

    x_axis = response.axis
    realizations = _get_realizations_data(response.realizations, x_axis)
    observations = []

    for obs in response.observations:
        observations += _get_observation_data(obs, x_axis)

    ensemble_plot = EnsemblePlotModel(
        realizations,
        observations,
        dict(
            xaxis={
                "title": "Index",
            },
            yaxis={
                "title": "Unit TODO",
            },
            margin={"l": 40, "b": 40, "t": 10, "r": 0},
            hovermode="closest",
            uirevision=True,
        ),
    )
    return ensemble_plot


def response_controller(parent, app):
    @app.callback(
        Output(parent.uuid("response-selector"), "options"), [Input("url", "search")]
    )
    def _set_response_options(query):
        queries = parse_url_query(query)
        if not "ensemble_id" in queries:
            return []
        ensemble_id = queries["ensemble_id"]
        ensemble = parent.ensembles.get(ensemble_id, EnsembleModel(ref_url=get_ensemble_url(ensemble_id)))
        parent.ensembles[ensemble_id] = ensemble
        return [
            {"label": response, "value": {"response":response, "ensemble_id":ensemble_id}}
            for response in ensemble.responses
        ]


    @app.callback(
        Output(parent.uuid("response-selector"), "value"),
        [Input(parent.uuid("response-selector"), "options")],
    )
    def _set_responses_value(available_options):
        if available_options:
            return available_options[0]["value"]
        return ""

    @app.callback(
        Output(
            {"id": parent.uuid("response-graphic"), "type": parent.uuid("graph")},
            "figure",
        ),
        [
            Input(parent.uuid("response-selector"), "value"),
            Input(parent.uuid("selection-store"), "data"),
        ],
    )
    def _update_graph(value, selected_realizations):

        if value["response"] in [None, ""] and parent.ensemble_plot is None:
            raise PreventUpdate
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate
        else:
            select_update = ctx.triggered[0]["prop_id"].split(".")[0] == parent.uuid(
                "selection-store"
            )

        if select_update:
            parent.ensemble_plot.selection = selected_realizations
        else:
            ensemble_id = value["ensemble_id"]
            ensemble = parent.ensembles.get(ensemble_id, None)
            parent.ensemble_plot = _create_response_model(ensemble.responses[value["response"]])

        return parent.ensemble_plot.repr