"""Choices shared by all pages: area type, area and time frame.

They live in plain session_state keys (sel_type, sel_area, sel_period). The widgets (w_*) only show them and write back
with a callback, because Streamlit drops a widget's value when its page is not shown.
"""
import streamlit as st

AREAS = {"EL": [f"EL {i}" for i in range(1, 6)], "VASS": [f"VASS {i}" for i in range(1, 4)], "NO": ["Norway"]}
TYPE_NAMES = {"EL": "Price areas (EL)", "VASS": "Water areas (VASS)", "NO": "Whole Norway (NO)"}
DEFAULT_AREA = "EL 3"

TYPE_HELP = ("**EL**: the five electricity price areas (NO1 to NO5). **VASS**: the three watercourse areas (river basins) that NVE uses "
             "for the reservoir statistics. **NO**: Norway as one area. The choice is shared by all pages.")
AREA_HELP = "The area you choose is used on all pages. On the Home page you can also click an area on the map."
PERIOD_HELP = "First and last month. Pages with a time frame (Reservoirs, Exchange rates, Forecast and the map) start with this choice."


def init():
    """Called on every rerun, before the page runs."""
    st.session_state.setdefault("sel_type", "EL")
    st.session_state.setdefault("sel_area", DEFAULT_AREA)


def area():
    return st.session_state.sel_area


def zone():
    """NO1 to NO5 for a price area (the name used for flows), otherwise None."""
    ss = st.session_state
    return "NO" + ss.sel_area.split()[1] if ss.sel_type == "EL" else None


def period():
    """(first month, last month) as 'YYYY-MM', or None until a slider has been shown."""
    return st.session_state.get("sel_period")


def set_area(name):
    """Store an area (e.g. from a map click) for all pages."""
    st.session_state.sel_type = name.split()[0] if name != "Norway" else "NO"
    st.session_state.sel_area = name


def reset():
    """Back to the default area; the slider sets its default again on the next run."""
    ss = st.session_state
    ss.sel_type, ss.sel_area = "EL", DEFAULT_AREA
    for key in ("sel_period", "w_period", "map_colour"):
        ss.pop(key, None)


def _pick_type():
    st.session_state.sel_type = st.session_state.w_type
    st.session_state.sel_area = AREAS[st.session_state.sel_type][0]      # the area must belong to the type


def _pick_area():
    st.session_state.sel_area = st.session_state.w_area


def _check(types):
    # the page may not support the stored type; the area must match the type
    ss = st.session_state
    if ss.sel_type not in types:
        ss.sel_type = types[0]
        ss.sel_area = AREAS[types[0]][0]
    if ss.sel_area not in AREAS[ss.sel_type]:
        ss.sel_area = AREAS[ss.sel_type][0]


def area_picker(types=("EL", "VASS", "NO"), where=st):
    """Area type and area selectors."""
    _check(types)
    st.session_state.w_type, st.session_state.w_area = st.session_state.sel_type, st.session_state.sel_area
    where.radio("Area type", types, key="w_type", format_func=TYPE_NAMES.get, horizontal=True, on_change=_pick_type, help=TYPE_HELP)
    where.selectbox("Area", AREAS[st.session_state.sel_type], key="w_area", on_change=_pick_area, help=AREA_HELP)
    return st.session_state.sel_type, st.session_state.sel_area


def type_picker(where=st):
    """Area type only (pages that show every area of a type)."""
    st.session_state.w_type = st.session_state.sel_type
    where.radio("Area type", list(AREAS), key="w_type", format_func=TYPE_NAMES.get, horizontal=True, on_change=_pick_type, help=TYPE_HELP)
    return st.session_state.sel_type


def _pick_period():
    st.session_state.sel_period = st.session_state.w_period


def period_slider(options, where=st, label="Time frame (months)"):
    """Range slider over the months in 'options' ('YYYY-MM')."""
    current = st.session_state.get("sel_period")
    if current is None or not all(m in options for m in current):      # default: last 12 months
        st.session_state.sel_period = (options[max(0, len(options) - 12)], options[-1])
    # value= (not the key) gives the two handles
    where.select_slider(label, options=options, value=st.session_state.sel_period, key="w_period", on_change=_pick_period, help=PERIOD_HELP)
    return st.session_state.sel_period
