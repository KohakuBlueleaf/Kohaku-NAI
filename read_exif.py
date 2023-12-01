import click
import piexif
import PIL.Image


@click.command()
@click.argument("path", type=click.Path(exists=True))
def main(path: str):
    img = PIL.Image.open(path)
    exif_dict = piexif.load(img.info["exif"])
    # print(img.info)
    print(exif_dict)


if __name__ == "__main__":
    main()
