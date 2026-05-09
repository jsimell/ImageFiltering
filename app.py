import uuid
import streamlit as st
import colorsys
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
if "applied_filters" not in st.session_state:
    st.session_state.applied_filters = []

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
    if case == "selective colour":
        return filters.selective_colour(image, params)

    elif case == "cartoon":
        return filters.cartoon(image, params)
        
    elif case == "vintage film":
        return filters.vintage_film(image, params)
    
    elif case == "bilateral":
        return filters.bilateral(image, params)

    elif case == "pencil sketch":
        return filters.pencil_sketch(image, params)

    return image


# Applies the selected filters to the image in the UI
def apply_selected_filters():
    result = st.session_state.image.copy()
    for filter_item in st.session_state.applied_filters:
        result = apply_filter(result, filter_item["name"], filter_item["params"])
    st.session_state.filtered_image = result


def update_filters_with_spinner(spinner_placeholder):
    _, center_col, _ = spinner_placeholder.columns([1, 2, 1])
    with center_col:
        with st.spinner("Updating filters...", width="stretch"):
            apply_selected_filters()

    spinner_placeholder.empty()


def get_applied_filter(filter_name):
    for filter_item in st.session_state.applied_filters:
        if filter_item["name"] == filter_name:
            return filter_item
    return None


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
            st.session_state.applied_filters = []
            st.rerun()


# ---------- View 2: Image Uploaded ----------
else:

    if st.session_state.filtered_image is None:
        st.session_state.filtered_image = st.session_state.image.copy()

    col_left, col_middle, col_right = st.columns([1.75, 1.75, 1])
    should_rerun = False

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
                st.session_state.applied_filters = []
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
        st.subheader("Current Filters", divider="gray")
        current_filters_spinner = st.empty()
        if not st.session_state.applied_filters:
            st.markdown("<p style='text-align: center;'>None.</p>", unsafe_allow_html=True)
        else:
            for f in st.session_state.applied_filters:
                st.markdown(f"- **{f['name']}** with parameters: {f['params']}")
                # For aligning the Remove button to the center
                _, button_col, _ = st.columns([0.75, 1, 0.75])
                # Button for removing the filter from the applied filters list
                with button_col:
                    if st.button("Remove", key=f"remove_{f['id']}", type="secondary", use_container_width=True):
                        st.session_state.applied_filters.remove(f)
                        update_filters_with_spinner(current_filters_spinner)
                        should_rerun = True
                        break

        st.write("") # Add some spacing
        st.subheader("Apply/Modify Filters", divider="gray")

        filter_choice = st.selectbox(
            "Choose filter",
            ["None", "Selective Colour", "Cartoon", "Bilateral", "Vintage Film", "Pencil Sketch"],
            key="new_filter_choice",
        )

        # Dynamic parameters depending on filter.
        # These define what the user can change for each filter in the UI, and are passed to the filter functions in filters.py when "Apply Filter" is pressed.
        # NOTE: I just added some initial parameters for demonstration that can be changed to what is needed for your filters
        if filter_choice == "Selective Colour":
            params["tolerance"] = st.slider("Tolerance", 0, 30, 5, key="selective_tolerance")
            hue = st.slider("Target color hue", 0.00, 1.00, 0.00, step=0.01, key="selective_hue")
            # Display a color gradient block below the slider to help users choose the hue
            st.markdown(
                """
                <div style="
                    width: 100%;
                    height: 16px;
                    margin-top: -3.28rem;
                    z-index: -100;
                    border-radius: 8px;
                    border: 1px solid #ccc;
                    background: linear-gradient(
                        to right,
                        #ff0000 0%,
                        #ffff00 17%,
                        #00ff00 33%,
                        #00ffff 50%,
                        #0000ff 67%,
                        #ff00ff 83%,
                        #ff0000 100%
                    );
                    margin-bottom: 0.75rem;
                    pointer-events: none;
                "></div>
                """,
                unsafe_allow_html=True,
            )

            r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
            rgb = (int(r * 255), int(g * 255), int(b * 255))
            params["color"] = '#%02x%02x%02x' % rgb

            st.markdown(
                f"""
                  <div style="display: flex; flex-direction: row; gap: 1rem; align-items: center; justify-content: space-between; margin-bottom: 2rem; margin-top: -1rem;">
                    <p style="margin: 0;">Selected hue: <code style="color: white">{params["color"]}</code></p>
                    <div style="background-color: {params["color"]}; height: 40px; width: 40px; border-radius: 8px;"></div>
                  </div>
                """,
                unsafe_allow_html=True,
            )

        elif filter_choice == "Cartoon":
            params["color_levels"] = st.slider("Color Levels", 3, 8, 4)
            params["edges"] = st.slider("Edges Intensity", 20, 100, 50)
            
        elif filter_choice == "Bilateral":
            params["radius"] = st.slider("Radius", 1, 7, 4, step=1)
            params["sigma_spatial"] = st.slider("Sigma Spatial", 1.0, 12.0, 5.0, 0.1)
            params["sigma_range"] = st.slider("Sigma Range", 0.01, 0.4, 0.15, 0.01)

        elif filter_choice == "Vintage Film":
            params["contrast"] = st.slider("Contrast", 0.4, 1.2, 0.75, 0.01)
            params["warmth"] = st.slider("Warmth", 0.0, 0.6, 0.25, 0.01)
            params["noise_amount"] = st.slider("Film Grain", 0.0, 0.2, 0.05, 0.005)
            params["noise_clip"] = st.slider("Noise Intensity", 0.0, 1.0, 0.5, 0.01)
            # params["grain_scale"] = st.slider("Grain Scale", 1.0, 10.0, 5.0, 0.1)

        elif filter_choice == "Pencil Sketch":
            params["intensity"] = st.slider("Sketch intensity", 1, 5, 3, key="pencil_intensity")

        existing_filter = get_applied_filter(filter_choice) if filter_choice != "None" else None

        if filter_choice != "None":
            # If the filter has already been applied, the button should serve as a parameter update button
            action_label = "Modify Filter" if existing_filter is not None else "Apply Filter"

            # For aligning the Apply Filter button
            _, button_col, _ = st.columns([0.5, 2, 0.5])

            with button_col:
                if st.button(action_label, type="primary", use_container_width=True, key="apply_new_filter"):
                    if existing_filter is not None:
                        existing_filter["params"] = params.copy()
                    else:
                        st.session_state.applied_filters.append({"id": str(uuid.uuid4()), "name": filter_choice, "params": params.copy()})
                    update_filters_with_spinner(current_filters_spinner)
                    st.rerun()

        has_unapplied_changes = (
            # Check if current filter is in applied filters list with the selected parameters
            filter_choice != "None"
            and (existing_filter is None or existing_filter["params"] != params)
        )

        if has_unapplied_changes:
            if existing_filter is not None:
                st.info("Press 'Modify Filter' to modify the parameters of the applied filter.", icon=":material/info:")
            else:
                st.info("Press 'Apply Filter' to add the filter to the applied filters list.", icon=":material/info:")

        if should_rerun:
            st.rerun()
