import requests
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from colorthief import ColorThief, MMCQ


def get_jwt(domain, client_id, client_secret):
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post(f'{domain}/oauth/token/', headers=headers, data=data)
    return response.json()

def get_client(domain, client_id, client_secret):
    jwt = get_jwt(domain, client_id, client_secret)
    transport = RequestsHTTPTransport(url=f'{domain}/graphql',
                                      headers={'Authorization': f'Bearer {jwt["access_token"]}'})
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client



class ColorThiefWithWhite(ColorThief):
    """Color thief patched so it also looks for white pixels - because we are interested in alle Farben [all colors]"""

    def get_palette(self, color_count=10, quality=10):
        """Build a color palette.  We are using the median cut algorithm to
        cluster similar colors.
        :param color_count: the size of the palette, max number of colors
        :param quality: quality settings, 1 is the highest quality, the bigger
                        the number, the faster the palette generation, but the
                        greater the likelihood that colors will be missed.
        :return list: a list of tuple in the form (r, g, b)
        """
        image = self.image.convert('RGBA')
        width, height = image.size
        pixels = image.getdata()
        pixel_count = width * height
        valid_pixels = []
        for i in range(0, pixel_count, quality):
            r, g, b, a = pixels[i]
            # If pixel is mostly opaque and not white
            if a >= 125:
                valid_pixels.append((r, g, b))

        # Send array to quantize function which clusters values
        # using median cut algorithm
        cmap = MMCQ.quantize(valid_pixels, color_count)
        return cmap.palette