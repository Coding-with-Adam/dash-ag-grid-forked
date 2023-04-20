from dash import Dash, html, Output, Input, no_update, ALL, ctx, Patch
import dash_ag_grid as dag
import plotly.express as px
import pandas as pd
import json
from dash.testing.wait import until

from . import utils


df = px.data.election()
default_display_cols = ["district_id", "district", "winner"]


def test_pa001_pagination(dash_duo):
    app = Dash(__name__)

    df = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/ag-grid/olympic-winners.csv"
    )

    opts = ['first', 'next', 'previous', 'last', 40]

    # basic columns definition with column defaults
    columnDefs = [
        {"field": "country"},
        {"field": "year"},
        {"field": "athlete"},
        {"field": "age"},
        {"field": "date"},
        {"field": "sport"},
        {"field": "total"},
    ]

    app.layout = html.Div(
        [
            dag.AgGrid(
                id="grid",
                columnDefs=columnDefs,
                rowData=df.to_dict("records"),
                columnSize="sizeToFit",
                defaultColDef={"resizable": True, "sortable": True, "filter": True},
                dashGridOptions={"pagination": True},
            ),
            html.Div(id='grid-info'),
            html.Button(id='changeSize', children='changeSize')

        ] + [html.Button(id={'type': 'nav', 'index': x}, children=x) for x in opts],
        style={"margin": 20},
    )

    @app.callback(Output('grid', 'dashGridOptions'), Input('changeSize', 'n_clicks'))
    def updatePageSize(n):
        if n:
            opts = Patch()
            opts['paginationPageSize'] = 10 * n
            return opts
        return no_update

    @app.callback(Output("grid-info", "children"), Input("grid", "paginationInfo"))
    def update_height(h):
        if h:
            return json.dumps(h)
        return no_update

    @app.callback(Output('grid', 'paginationGoTo'), Input({'type': 'nav', 'index': ALL}, 'n_clicks'))
    def updatePage(_):
        if ctx.triggered:
            return ctx.triggered_id['index']
        return no_update

    dash_duo.start_server(app)

    grid = utils.Grid(dash_duo, "grid")

    grid.wait_for_cell_text(0,0, 'United States')
    oldValue = ''
    until(lambda: oldValue != dash_duo.find_element('#grid-info').text, timeout=3)
    oldValue = dash_duo.find_element('#grid-info').text
    dash_duo.find_element('.ag-paging-button[aria-label="Last Page"]').click()
    until(lambda: oldValue != dash_duo.find_element('#grid-info').text, timeout=3)
    oldValue = dash_duo.find_element('#grid-info').text

    btns = dash_duo.find_elements("button")
    for x in range(len(btns)):
        btns[x].click()
        until(lambda: oldValue != dash_duo.find_element('#grid-info').text, timeout=3)
        oldValue = dash_duo.find_element('#grid-info').text

    assert oldValue == '{"isLastPageFound": true, "pageSize": 10, ' \
                       '"currentPage": 40, "totalPages": 862, ' \
                       '"rowCount": 8618}'