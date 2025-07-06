# components.py
import reflex as rx


def loader(is_loading: bool):
    return rx.center(
        rx.html(
            """
            <iframe src="https://lottie.host/embed/c5ea05d5-a299-450c-af25-0ae9c7fc2fba/4DgOchkQ49.lottie "
                    style="width: 380px; height: 380px; border: none; background: none;" 
                    allowfullscreen>
            </iframe>
            """
        ),
        style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100vw",
            "height": "100vh",
            "backgroundColor": "rgba(255,255,255,0.6)",
            "backdropFilter": "blur(6px)",
            "zIndex": "9999",
            "pointerEvents": "none",
            "opacity": rx.cond(is_loading, "1", "0"),  # Accept is_loading as a prop
            "transition": "opacity 0.5s ease-in-out",
        }
    )