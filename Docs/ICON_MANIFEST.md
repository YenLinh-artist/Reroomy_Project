# Icon manifest — Re:Room

Most icons in `store/static/store/icons/` are Lucide SVG assets from the official Lucide repository. `wardrobe.svg` is from the matching Lucide Lab collection discovered through Iconify. The set covers navigation, status, search, room planning and several common furniture categories.

License: ISC. Lucide's license text is preserved in `store/static/store/icons/LICENSE.txt`. Source repository: https://github.com/lucide-icons/lucide. Individual source files use the matching path `https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/<name>.svg`.

Current furniture-specific icons: `sofa.svg`, `armchair.svg`, `bed-double.svg`, `lamp-floor.svg`, `table-2.svg`, `wardrobe.svg`. The other icons are common interface symbols: `archive`, `arrow-right`, `bell`, `boxes`, `check`, `door-open`, `file-text`, `folder`, `heart`, `layout-dashboard`, `menu`, `message-circle`, `package`, `receipt`, `ruler`, `search`, `settings`, `share-2`, `shopping-bag`, `star`, `ticket`, `user-round`, and `users-round`.

`wardrobe.svg` comes from Iconify set `lucide-lab:wardrobe`, by Lucide Contributors, under ISC; source: https://icon-sets.iconify.design/lucide-lab/wardrobe/. The remaining gaps are shelf/bookcase, mirror, and laundry basket. Their candidate Iconify assets were not added because the surfaced bookshelf icon was a different filled style, and a consistent outline item with a verified license was not confirmed. Recheck each candidate's collection license before adding it.

Usage: reference with Django static, for example `{% static 'store/icons/sofa.svg' %}`. Do not recolor or redraw paths inline; use CSS filters on the image element when needed.
