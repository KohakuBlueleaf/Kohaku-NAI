import piexif
import piexif.helper
import click
from PIL import Image


def read_info_from_image(image: Image.Image) -> tuple[str | None, dict]:
    """
    https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/cf2772fab0af5573da775e7437e6acdca424f26e/modules/images.py#L723-L761
    """
    items = (image.info or {}).copy()

    geninfo = items.pop("parameters", None)

    if "exif" in items:
        exif_data = items["exif"]
        try:
            exif = piexif.load(exif_data)
        except OSError:
            # memory / exif was not valid so piexif tried to read from a file
            exif = None
        exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b"")
        try:
            exif_comment = piexif.helper.UserComment.load(exif_comment)
        except ValueError:
            exif_comment = exif_comment.decode("utf8", errors="ignore")

        if exif_comment:
            items["exif comment"] = exif_comment
            geninfo = exif_comment
    elif "comment" in items:  # for gif
        geninfo = items["comment"].decode("utf8", errors="ignore")

    return geninfo, items


@click.command()
@click.argument("image", type=click.Path(exists=True))
def main(image: str):
    image = Image.open(image)
    geninfo, items = read_info_from_image(image)
    print(geninfo)
    print(items)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
