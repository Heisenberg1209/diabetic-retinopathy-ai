from pathlib import Path

from PIL import Image, ImageStat, ImageFilter


def assess_image_quality(image_path: str) -> dict:
    """
    Performs a basic technical quality assessment of a retinal image.

    This is a prototype quality checker.
    The final ML-based quality model can replace or extend this function.
    """

    path = Path(image_path)

    # Check whether file exists
    if not path.exists():
        return {
            "score": 0,
            "status": "ungradable",
            "feedback": "Image file not found."
        }

    try:
        with Image.open(path) as image:

            # Convert to RGB
            image = image.convert("RGB")
            width, height = image.size

            # --------------------------------
            # 1. Resolution score
            # --------------------------------
            pixels = width * height

            if pixels >= 1_000_000:
                resolution_score = 100
            elif pixels >= 500_000:
                resolution_score = 80
            elif pixels >= 250_000:
                resolution_score = 60
            else:
                resolution_score = 30

            # --------------------------------
            # 2. Brightness score
            # --------------------------------
            grayscale = image.convert("L")
            stats = ImageStat.Stat(grayscale)
            brightness = stats.mean[0]

            if 60 <= brightness <= 200:
                brightness_score = 100
            elif 40 <= brightness <= 220:
                brightness_score = 75
            else:
                brightness_score = 40

            # --------------------------------
            # 3. Contrast score
            # --------------------------------
            contrast = stats.stddev[0]

            if contrast >= 45:
                contrast_score = 100
            elif contrast >= 30:
                contrast_score = 75
            elif contrast >= 20:
                contrast_score = 50
            else:
                contrast_score = 25

            # --------------------------------
            # 4. Basic sharpness score
            # --------------------------------
            edges = grayscale.filter(ImageFilter.FIND_EDGES)
            edge_stats = ImageStat.Stat(edges)
            sharpness = edge_stats.stddev[0]

            if sharpness >= 18:
                sharpness_score = 100
            elif sharpness >= 12:
                sharpness_score = 75
            elif sharpness >= 7:
                sharpness_score = 50
            else:
                sharpness_score = 25

            # --------------------------------
            # Overall quality score
            # --------------------------------
            quality_score = round(
                0.25 * resolution_score
                + 0.25 * brightness_score
                + 0.25 * contrast_score
                + 0.25 * sharpness_score
            )

            # --------------------------------
            # Determine status
            # --------------------------------
            if quality_score >= 70:
                status = "gradable"
                feedback = "Image quality is acceptable for screening."

            elif quality_score >= 50:
                status = "borderline"
                feedback = (
                    "Image quality is borderline. "
                    "Enhancement is recommended before screening."
                )

            else:
                status = "ungradable"
                feedback = (
                    "Image quality is insufficient. "
                    "Please recapture the retinal image."
                )

            return {
                "score": quality_score,
                "status": status,
                "feedback": feedback,
                "details": {
                    "resolution": f"{width}x{height}",
                    "brightness": round(brightness, 2),
                    "contrast": round(contrast, 2),
                    "sharpness": round(sharpness, 2)
                }
            }

    except Exception as e:
        return {
            "score": 0,
            "status": "ungradable",
            "feedback": f"Unable to analyze image: {str(e)}"
        }