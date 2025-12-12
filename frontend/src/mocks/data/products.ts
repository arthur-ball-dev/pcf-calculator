/**
 * Mock Products Data
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * 100+ mock products with realistic data
 * distributed across all industry sectors.
 */

import { getAllCategoriesFlat } from './categories';

export interface MockProduct {
  id: string;
  code: string;
  name: string;
  description: string | null;
  unit: string;
  category: {
    id: string;
    code: string;
    name: string;
    industry_sector: string | null;
  } | null;
  manufacturer: string | null;
  country_of_origin: string | null;
  is_finished_product: boolean;
  relevance_score: number | null;
  created_at: string;
}

// Manufacturers by industry
// Note: Manufacturer names should not contain industry names like "Electronics"
// to avoid selector conflicts in UI tests
const manufacturers: Record<string, string[]> = {
  electronics: ['Apple Inc.', 'Samsung', 'Dell Technologies', 'HP Inc.', 'Lenovo', 'ASUS', 'Acer'],
  apparel: ['Nike Inc.', 'Adidas AG', 'H&M', 'Zara', 'Uniqlo', 'Levi Strauss', 'Gap Inc.'],
  automotive: ['Toyota Motor', 'Volkswagen AG', 'Ford Motor', 'General Motors', 'Tesla Inc.', 'BMW AG'],
  construction: ['HeidelbergCement', 'LafargeHolcim', 'US Steel', 'Weyerhaeuser', 'Boise Cascade'],
  food_beverage: ['Nestle SA', 'PepsiCo', 'Coca-Cola', 'Danone', 'Mondelez', 'General Mills'],
  chemicals: ['BASF SE', 'Dow Chemical', 'DuPont', 'LyondellBasell', 'SABIC'],
  machinery: ['Caterpillar Inc.', 'Siemens AG', 'ABB Ltd.', 'Fanuc Corp.', 'Komatsu Ltd.'],
  other: ['Generic Manufacturer', 'Unknown', 'Various'],
};

// Countries of origin
const countries = ['US', 'CN', 'DE', 'JP', 'KR', 'TW', 'VN', 'BD', 'MX', 'GB', 'FR', 'IT'];

// Units by category type
const unitsByIndustry: Record<string, string[]> = {
  electronics: ['unit', 'pcs'],
  apparel: ['unit', 'pcs'],
  automotive: ['unit', 'pcs'],
  construction: ['kg', 'm3', 'unit'],
  food_beverage: ['kg', 'L', 'unit'],
  chemicals: ['kg', 'L', 'm3'],
  machinery: ['unit', 'pcs'],
  other: ['unit', 'kg'],
};

// Product name templates by category
const productTemplates: Record<string, string[]> = {
  'ELEC-COMP-LAPTOP': ['Business Laptop', 'Gaming Laptop', 'Ultrabook', 'Workstation Laptop', 'Student Laptop'],
  'ELEC-COMP-DESKTOP': ['Office Desktop', 'Gaming Desktop', 'Workstation', 'All-in-One PC', 'Mini PC'],
  'ELEC-COMP-SERVER': ['Rack Server', 'Tower Server', 'Blade Server', 'Edge Server', 'Cloud Server'],
  'ELEC-MOBILE-PHONE': ['Flagship Smartphone', 'Mid-range Phone', 'Budget Smartphone', '5G Phone', 'Rugged Phone'],
  'ELEC-MOBILE-TABLET': ['Pro Tablet', 'Standard Tablet', 'Kids Tablet', 'E-Reader', 'Drawing Tablet'],
  'ELEC-DISPLAY': ['4K Monitor', 'Gaming Monitor', 'Ultrawide Display', 'Curved Monitor', 'Portable Monitor'],
  'APRL-TOPS-TSHIRT': ['Cotton T-Shirt', 'Organic Cotton Tee', 'Performance T-Shirt', 'Graphic Tee', 'Basic Tee'],
  'APRL-TOPS-SHIRT': ['Oxford Shirt', 'Dress Shirt', 'Casual Button-Down', 'Linen Shirt', 'Flannel Shirt'],
  'APRL-BOTTOM-JEAN': ['Slim Fit Jeans', 'Regular Fit Denim', 'Relaxed Jeans', 'Stretch Jeans', 'Raw Denim'],
  'APRL-BOTTOM-PANT': ['Chino Pants', 'Dress Pants', 'Cargo Pants', 'Jogger Pants', 'Work Pants'],
  'APRL-OUTER': ['Winter Jacket', 'Rain Coat', 'Fleece Jacket', 'Down Puffer', 'Windbreaker'],
  'AUTO-VEH': ['Sedan', 'SUV', 'Electric Vehicle', 'Pickup Truck', 'Crossover'],
  'AUTO-PARTS-BATT': ['Lead-Acid Battery', 'Lithium-Ion Battery', 'AGM Battery', 'EV Battery Pack', 'Hybrid Battery'],
  'AUTO-PARTS-TIRE': ['All-Season Tire', 'Winter Tire', 'Performance Tire', 'Off-Road Tire', 'Run-Flat Tire'],
  'CONST-MAT-STEEL': ['Structural Steel Beam', 'Rebar', 'Steel Sheet', 'Steel Pipe', 'Steel Plate'],
  'CONST-MAT-CONC': ['Ready-Mix Concrete', 'Precast Concrete', 'Concrete Block', 'Cement', 'Mortar Mix'],
  'CONST-MAT-WOOD': ['Lumber', 'Plywood', 'OSB Board', 'MDF Panel', 'Engineered Wood'],
  'FOOD-BEV': ['Bottled Water', 'Soft Drink', 'Juice', 'Energy Drink', 'Sports Drink'],
  'FOOD-PKG': ['Cereal Box', 'Snack Bar', 'Frozen Meal', 'Canned Soup', 'Pasta Package'],
  'CHEM-IND': ['Sulfuric Acid', 'Sodium Hydroxide', 'Ammonia', 'Chlorine', 'Ethylene'],
  'CHEM-SPEC': ['Adhesive', 'Coating', 'Sealant', 'Catalyst', 'Surfactant'],
  'MACH-IND': ['CNC Machine', 'Hydraulic Press', 'Conveyor System', 'Industrial Robot', 'Compressor'],
  'MACH-PREC': ['3D Printer', 'Laser Cutter', 'CMM Machine', 'EDM Machine', 'Precision Lathe'],
};

// Generate a UUID v4
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Generate products
function generateProducts(): MockProduct[] {
  const allCategories = getAllCategoriesFlat();
  const leafCategories = allCategories.filter((cat) => cat.children.length === 0);
  const products: MockProduct[] = [];
  let productIndex = 0;

  // Generate products for each leaf category
  for (const category of leafCategories) {
    const templates = productTemplates[category.code] || [`${category.name} Product`];
    const industry = category.industry_sector || 'other';
    const mfrs = manufacturers[industry] || manufacturers.other;
    const units = unitsByIndustry[industry] || unitsByIndustry.other;

    // Generate 3-6 products per leaf category
    const numProducts = Math.floor(Math.random() * 4) + 3;

    for (let i = 0; i < numProducts; i++) {
      const template = templates[i % templates.length];
      const variant = i > 0 ? ` - Variant ${i}` : '';

      products.push({
        id: generateUUID(),
        code: `PROD-${String(productIndex + 1).padStart(4, '0')}`,
        name: `${template}${variant}`,
        description: `High-quality ${template.toLowerCase()} from ${category.name} category. Manufactured with sustainable practices.`,
        unit: units[Math.floor(Math.random() * units.length)],
        category: {
          id: category.id,
          code: category.code,
          name: category.name,
          industry_sector: category.industry_sector,
        },
        manufacturer: mfrs[Math.floor(Math.random() * mfrs.length)],
        country_of_origin: countries[Math.floor(Math.random() * countries.length)],
        is_finished_product: Math.random() > 0.2, // 80% finished products
        relevance_score: null,
        created_at: new Date(
          Date.now() - Math.floor(Math.random() * 365 * 24 * 60 * 60 * 1000)
        ).toISOString(),
      });
      productIndex++;
    }
  }

  // Ensure we have at least 100 products
  while (products.length < 100) {
    const category = leafCategories[Math.floor(Math.random() * leafCategories.length)];
    const industry = category.industry_sector || 'other';
    const mfrs = manufacturers[industry] || manufacturers.other;
    const units = unitsByIndustry[industry] || unitsByIndustry.other;

    products.push({
      id: generateUUID(),
      code: `PROD-${String(productIndex + 1).padStart(4, '0')}`,
      name: `${category.name} Product ${productIndex + 1}`,
      description: `Standard product in ${category.name} category.`,
      unit: units[Math.floor(Math.random() * units.length)],
      category: {
        id: category.id,
        code: category.code,
        name: category.name,
        industry_sector: category.industry_sector,
      },
      manufacturer: mfrs[Math.floor(Math.random() * mfrs.length)],
      country_of_origin: countries[Math.floor(Math.random() * countries.length)],
      is_finished_product: Math.random() > 0.3,
      relevance_score: null,
      created_at: new Date(
        Date.now() - Math.floor(Math.random() * 365 * 24 * 60 * 60 * 1000)
      ).toISOString(),
    });
    productIndex++;
  }

  // Add some products with "laptop" in name for search testing
  const laptopProducts = [
    {
      id: generateUUID(),
      code: 'PROD-LAPTOP-001',
      name: 'ProBook Laptop 14-inch',
      description: 'Professional laptop with aluminum chassis and long battery life',
      unit: 'unit',
      category: {
        id: '550e8400-e29b-41d4-a716-446655440003',
        code: 'ELEC-COMP-LAPTOP',
        name: 'Laptops',
        industry_sector: 'electronics',
      },
      manufacturer: 'HP Inc.',
      country_of_origin: 'CN',
      is_finished_product: true,
      relevance_score: null,
      created_at: new Date().toISOString(),
    },
    {
      id: generateUUID(),
      code: 'PROD-LAPTOP-002',
      name: 'ThinkPad Laptop Enterprise',
      description: 'Enterprise-grade laptop with security features',
      unit: 'unit',
      category: {
        id: '550e8400-e29b-41d4-a716-446655440003',
        code: 'ELEC-COMP-LAPTOP',
        name: 'Laptops',
        industry_sector: 'electronics',
      },
      manufacturer: 'Lenovo',
      country_of_origin: 'CN',
      is_finished_product: true,
      relevance_score: null,
      created_at: new Date().toISOString(),
    },
  ];

  return [...products, ...laptopProducts];
}

export const mockProducts: MockProduct[] = generateProducts();

// Filter helper for products
export function filterProducts(
  products: MockProduct[],
  filters: {
    query?: string;
    category_id?: string;
    industry?: string;
    manufacturer?: string;
    country_of_origin?: string;
    is_finished_product?: boolean;
  }
): MockProduct[] {
  let filtered = [...products];

  if (filters.query) {
    const query = filters.query.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query) ||
        p.code.toLowerCase().includes(query)
    );
    // Add relevance scores
    filtered = filtered.map((p) => ({
      ...p,
      relevance_score:
        p.name.toLowerCase().includes(query)
          ? 0.95
          : p.description?.toLowerCase().includes(query)
          ? 0.7
          : 0.5,
    }));
    // Sort by relevance
    filtered.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
  }

  if (filters.category_id) {
    filtered = filtered.filter((p) => p.category?.id === filters.category_id);
  }

  if (filters.industry) {
    filtered = filtered.filter(
      (p) => p.category?.industry_sector === filters.industry
    );
  }

  if (filters.manufacturer) {
    const mfr = filters.manufacturer.toLowerCase();
    filtered = filtered.filter((p) =>
      p.manufacturer?.toLowerCase().includes(mfr)
    );
  }

  if (filters.country_of_origin) {
    filtered = filtered.filter(
      (p) => p.country_of_origin === filters.country_of_origin
    );
  }

  if (filters.is_finished_product !== undefined) {
    filtered = filtered.filter(
      (p) => p.is_finished_product === filters.is_finished_product
    );
  }

  return filtered;
}
