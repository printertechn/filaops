# Database Seeding Guide

FilaOps includes a seed script to populate your database with example data and a comprehensive materials list.

## What Gets Seeded

### 1. Example Items (One Per Category)
The script creates example items for each standard category:
- **PLA** - Example PLA Product
- **PETG** - Example PETG Product  
- **ABS** - Example ABS Product
- **TPU** - Example TPU Product
- **Boxes** - Example Shipping Box
- **Bags** - Example Poly Bag
- **Fasteners** - Example Fastener Set
- **Inserts** - Example Heat Set Insert
- **Standard Products** - Example Standard Product
- **Custom Products** - Example Custom Product

These help you understand how categories work and provide examples for your own products.

### 2. Comprehensive Materials List

#### Material Types (8 types):
- **PLA Basic** - Standard PLA ($20/kg)
- **PLA Matte** - Matte finish PLA ($22/kg)
- **PLA Silk** - Glossy silk PLA ($25/kg)
- **PETG High Flow** - High-flow PETG ($24/kg)
- **ABS Basic** - ABS (requires enclosure, $22/kg)
- **ASA Basic** - UV-resistant ASA (requires enclosure, $28/kg)
- **TPU 95A** - Flexible TPU ($35/kg)
- **TPU 68D** - Rigid TPU ($38/kg)

#### Colors (14 colors):
- White, Black, Red, Blue, Green, Yellow, Orange, Purple, Pink, Gray, Silver, Gold, Transparent, Natural

All colors are linked to all material types, giving you **112 material+color combinations** ready to use!

## Running the Seed Script

### Option 1: From Project Root
```bash
python -m backend.scripts.seed_example_data
```

### Option 2: From Backend Directory
```bash
cd backend
python scripts/seed_example_data.py
```

### Option 3: Docker
```bash
docker-compose exec backend python -m backend.scripts.seed_example_data
```

## What Happens

1. **Checks for existing data** - Won't duplicate items that already exist
2. **Creates example items** - One per category with realistic pricing
3. **Creates material types** - All common 3D printing materials
4. **Creates colors** - Standard color palette
5. **Links materials to colors** - All combinations available

## After Seeding

- ✅ Example items appear in the Items page, organized by category
- ✅ Materials are available for quoting and inventory management
- ✅ You can immediately start creating quotes with material options
- ✅ Inventory can be tracked by material type and color

## Customization

You can edit `backend/scripts/seed_example_data.py` to:
- Add more material types
- Add more colors
- Change pricing
- Add more example items
- Customize material properties

## Notes

- The script is **idempotent** - safe to run multiple times
- Existing items/materials won't be overwritten
- You can delete seeded data and re-run if needed
- Materials are ready for production use immediately

---

**Tip:** Run this after initial database setup to get a head start on your inventory!

