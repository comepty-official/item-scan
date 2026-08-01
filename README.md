# FoodAI Dataset Builder (Admin Tool)

Offline-first **admin dataset builder** used to collect and organise food photos that
will later be used to train an AI food-recognition model.

* Python 3.13
* Kivy 2.3.1
* KivyMD 2.0.1.dev0 (new Material 3 API only - no deprecated widgets)

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

## What it does

1. **Capture Food** - opens the device camera, shows a preview, `Retake` / `Use Photo`.
2. **Food Details** - optional food name + description, free-form tags, optional USDA
   FoodData Central lookup when the machine is online.
3. **Save Dataset** - automatically creates `FoodAI_Dataset/<Food_Name>/` and writes
   `food_name_001.jpg`, `food_name_002.jpg`, ...
4. **Local database** - every record is appended to `food_db.json`.
5. **Food Library** - browse folders with image counts, open a folder, rename food,
   move / delete images, delete folder, edit description.
6. **Pending** - anything that failed to save is queued and can be retried.
7. **Settings** - theme, camera index, preview rotation, USDA API key.

Everything is stored on disk next to the project. No Django, no Firebase, no cloud.

## Folder structure

```
main.py
screens/     UI screens (one class per screen)
services/    camera, network and USDA integrations
storage/     filesystem / dataset management
database/    food_db.json access layer
utils/       paths, config, helpers
widgets/     reusable Material 3 widgets
assets/      icons / images
FoodAI_Dataset/  generated dataset root
food_db.json     generated database
```
