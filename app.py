import streamlit as st
from PIL import Image
import io
import filters

# NOTE: The app can be run by running `streamlit run app.py` in the terminal, which should open it in the browser automatically.

# ---------- Configuration ----------
st.set_page_config(layout="wide")

# ---------- Session state ----------
if "image" not in st.session_state:
    st.session_state.image = None
if "filtered_image" not in st.session_state:
    st.session_state.filtered_image = None
if "applied_filter_choice" not in st.session_state:
    st.session_state.applied_filter_choice = "None"
if "applied_params" not in st.session_state:
    st.session_state.applied_params = {}

def get_download_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


# ---------- Filtering ----------
# Applies the filter specified by filter_name to the image, using the parameters in params.
# Params for each filter depend on what the user can change in the UI, e.g. strength, kernel size, etc.
# Returns the filtered image
def apply_filter(image, filter_name, params):
    case = filter_name.lower()
    if case == "sharpness":
        return filters.sharpness(image, params)

    elif case == "selective colour":
        return filters.selective_colour(image, params)

    elif case == "gaussian blur":
        return filters.gaussian_blur(image, params)
    
    elif case == "vintage film":
        return filters.vintage_film(image, params)

    return image


# ---------- View 1: Starting View ----------
if st.session_state.image is None:

    _, col_middle, _ = st.columns([1, 2, 1])

    with col_middle:
        st.title("Image Filter Demo")

        uploaded_file = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"]
        )

        if uploaded_file is not None:
            st.session_state.image = Image.open(uploaded_file)
            st.session_state.filtered_image = st.session_state.image.copy()
            st.session_state.applied_filter_choice = "None"
            st.session_state.applied_params = {}
            st.rerun()


# ---------- View 2: Image Uploaded ----------
else:

    if st.session_state.filtered_image is None:
        st.session_state.filtered_image = st.session_state.image.copy()

    col_left, col_middle, col_right = st.columns([2, 2, 1])

    filter_choice = "None"
    params = {}


    # ---- LEFT COLUMN: Original image preview ----
    with col_left:
        st.image(
            st.session_state.image,
            caption="Original Image",
            use_container_width=True
        )

        _, button_col, _ = st.columns([2, 1.2, 2])

        with button_col:
            if st.button("Change image"):
                st.session_state.image = None
                st.session_state.filtered_image = None
                st.session_state.applied_filter_choice = "None"
                st.session_state.applied_params = {}
                st.rerun()

    # ---- MIDDLE COLUMN: Filtered image preview ----
    with col_middle:
        st.image(
            st.session_state.filtered_image,
            caption="Filtered Image",
            use_container_width=True
        )

        _, button_col, _ = st.columns([1.25, 1, 1.25])

        with button_col:
            st.download_button(
                "Download",
                data=get_download_bytes(st.session_state.filtered_image),
                file_name="filtered_image.png",
                mime="image/png",
                use_container_width=True,
            )

    # ---- RIGHT COLUMN: Filter controls ----
    with col_right:

        st.subheader("Filter Settings")

        filter_choice = st.selectbox(
            "Choose filter",
            ["None", "Sharpness", "Selective Colour", "Gaussian Blur", "Vintage Film"]
        )

        # Dynamic parameters depending on filter.
        # These define what the user can change for each filter in the UI, and are passed to the filter functions in filters.py when "Apply Filter" is pressed.
        # NOTE: I just added some initial parameters for demonstration that can be changed to what is needed for your filters
        if filter_choice == "Sharpness":
            slider = st.slider("Strength", 1.0, 5.99, 1.0)
            # Map the values "backwards" and with no negative values, so that the slider is more user friendly
            params["strength"] = 6.0 - slider

        elif filter_choice == "Selective Colour":
            params["color"] = st.color_picker("Pick a target color", "#838383")
            params["tolerance"] = st.slider("Tolerance", 0.0, 255.0, 10.0)

        elif filter_choice == "Gaussian Blur":
            params["kernel_size"] = st.slider("Kernel size (odd integer)", 1, 15, 3, step=2)

        elif filter_choice == "Vintage Film":
            params["param1"] = st.slider("Parameter name", 0.0, 10.0, 5.0)

        # For aligning the Apply Filter button
        _, button_col, _ = st.columns([0.75, 1, 0.75])

        with button_col:
            if st.button("Apply Filter"):
                st.session_state.filtered_image = apply_filter(
                    st.session_state.image.copy(),
                    filter_choice,
                    params,
                )
                st.session_state.applied_filter_choice = filter_choice
                st.session_state.applied_params = params.copy()
                st.rerun()

        has_unapplied_changes = (
            filter_choice != st.session_state.applied_filter_choice
            or params != st.session_state.applied_params
        )

        if has_unapplied_changes:
            st.info("Press 'Apply Filter' to see changes in the filtered image.", icon=":material/info:")