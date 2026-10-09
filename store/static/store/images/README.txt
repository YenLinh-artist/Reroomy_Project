RE:ROOM image slots

Folder: store/static/store/images/

Hero gallery files (the three uploaded room photos are used here):
- hero-room-bedroom.jpg
- hero-room-sofa.jpg
- hero-room-lounge.jpg

Replace those files with your preferred photos using the same filenames. The
hero gallery markup and image descriptions are in store/templates/index.html.
CSS object-position values there control which part of each photo stays visible.

Other image slots that can be replaced the same way:
- bedroom-combo.jpg: room photo in the decor-combo panel on the homepage.
- product-lounger.jpg, product-plush.jpg, product-desk.jpg, product-chair.jpg,
  product-lamp.jpg, product-phone-stand.jpg, product-duck-bin.jpg,
  product-bedside.jpg: product card photo slots. These are intentionally empty
  and show a placeholder for now. Copy a JPG into this folder with the matching
  filename; the product card will display it automatically. Product-to-filename
  mapping is in DEMO_PRODUCTS in store/views.py.
- signup-room.jpg and login-room.jpg: left-side images on the auth screens.

Use JPG files for replacements. Keep each filename exactly the same, or update
the matching image filename in store/views.py / store/templates/index.html.


Product detail page photos
- The detail page reuses the same image as its product card. For the sample
  products, replace product-lounger.jpg, product-plush.jpg, etc. above; the
  detail page will pick it up automatically.
- For products created in the admin area, upload the photo in the product form.
  Django stores those uploads under MEDIA_ROOT/products/ (served as /media/products/
  during local development). The detail template uses product.image_url.

Quick guide: copy your original photo into store/static/store/images/ and name
it exactly like the matching product filename above. Example: the bean bag photo
uses store/static/store/images/product-lounger.jpg. Refresh the page afterward.
