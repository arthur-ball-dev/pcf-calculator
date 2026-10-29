/**
 * Mock Product Categories Data
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Hierarchical category structure with 20+ categories
 * organized by industry sector.
 */

export interface MockCategory {
  id: string;
  code: string;
  name: string;
  level: number;
  industry_sector: string | null;
  product_count?: number;
  children: MockCategory[];
}

// Static UUIDs for consistent testing
const categoryIds = {
  // Electronics (Root)
  electronics: '550e8400-e29b-41d4-a716-446655440001',
  computers: '550e8400-e29b-41d4-a716-446655440002',
  laptops: '550e8400-e29b-41d4-a716-446655440003',
  desktops: '550e8400-e29b-41d4-a716-446655440004',
  servers: '550e8400-e29b-41d4-a716-446655440005',
  mobile: '550e8400-e29b-41d4-a716-446655440006',
  smartphones: '550e8400-e29b-41d4-a716-446655440007',
  tablets: '550e8400-e29b-41d4-a716-446655440008',
  displays: '550e8400-e29b-41d4-a716-446655440009',

  // Apparel (Root)
  apparel: '550e8400-e29b-41d4-a716-446655440010',
  tops: '550e8400-e29b-41d4-a716-446655440011',
  tshirts: '550e8400-e29b-41d4-a716-446655440012',
  shirts: '550e8400-e29b-41d4-a716-446655440013',
  bottoms: '550e8400-e29b-41d4-a716-446655440014',
  jeans: '550e8400-e29b-41d4-a716-446655440015',
  pants: '550e8400-e29b-41d4-a716-446655440016',
  outerwear: '550e8400-e29b-41d4-a716-446655440017',

  // Automotive (Root)
  automotive: '550e8400-e29b-41d4-a716-446655440020',
  vehicles: '550e8400-e29b-41d4-a716-446655440021',
  parts: '550e8400-e29b-41d4-a716-446655440022',
  batteries: '550e8400-e29b-41d4-a716-446655440023',
  tires: '550e8400-e29b-41d4-a716-446655440024',

  // Construction (Root)
  construction: '550e8400-e29b-41d4-a716-446655440030',
  materials: '550e8400-e29b-41d4-a716-446655440031',
  steel: '550e8400-e29b-41d4-a716-446655440032',
  concrete: '550e8400-e29b-41d4-a716-446655440033',
  wood: '550e8400-e29b-41d4-a716-446655440034',

  // Food & Beverage (Root)
  foodBeverage: '550e8400-e29b-41d4-a716-446655440040',
  beverages: '550e8400-e29b-41d4-a716-446655440041',
  packaged: '550e8400-e29b-41d4-a716-446655440042',

  // Chemicals (Root)
  chemicals: '550e8400-e29b-41d4-a716-446655440050',
  industrial: '550e8400-e29b-41d4-a716-446655440051',
  specialty: '550e8400-e29b-41d4-a716-446655440052',

  // Machinery (Root)
  machinery: '550e8400-e29b-41d4-a716-446655440060',
  industrial_eq: '550e8400-e29b-41d4-a716-446655440061',
  precision: '550e8400-e29b-41d4-a716-446655440062',
};

export const mockCategories: MockCategory[] = [
  // Electronics
  {
    id: categoryIds.electronics,
    code: 'ELEC',
    name: 'Electronics',
    level: 0,
    industry_sector: 'electronics',
    product_count: 450,
    children: [
      {
        id: categoryIds.computers,
        code: 'ELEC-COMP',
        name: 'Computers',
        level: 1,
        industry_sector: 'electronics',
        product_count: 120,
        children: [
          {
            id: categoryIds.laptops,
            code: 'ELEC-COMP-LAPTOP',
            name: 'Laptops',
            level: 2,
            industry_sector: 'electronics',
            product_count: 45,
            children: [],
          },
          {
            id: categoryIds.desktops,
            code: 'ELEC-COMP-DESKTOP',
            name: 'Desktops',
            level: 2,
            industry_sector: 'electronics',
            product_count: 35,
            children: [],
          },
          {
            id: categoryIds.servers,
            code: 'ELEC-COMP-SERVER',
            name: 'Servers',
            level: 2,
            industry_sector: 'electronics',
            product_count: 40,
            children: [],
          },
        ],
      },
      {
        id: categoryIds.mobile,
        code: 'ELEC-MOBILE',
        name: 'Mobile Devices',
        level: 1,
        industry_sector: 'electronics',
        product_count: 200,
        children: [
          {
            id: categoryIds.smartphones,
            code: 'ELEC-MOBILE-PHONE',
            name: 'Smartphones',
            level: 2,
            industry_sector: 'electronics',
            product_count: 120,
            children: [],
          },
          {
            id: categoryIds.tablets,
            code: 'ELEC-MOBILE-TABLET',
            name: 'Tablets',
            level: 2,
            industry_sector: 'electronics',
            product_count: 80,
            children: [],
          },
        ],
      },
      {
        id: categoryIds.displays,
        code: 'ELEC-DISPLAY',
        name: 'Displays & Monitors',
        level: 1,
        industry_sector: 'electronics',
        product_count: 130,
        children: [],
      },
    ],
  },
  // Apparel
  {
    id: categoryIds.apparel,
    code: 'APRL',
    name: 'Apparel',
    level: 0,
    industry_sector: 'apparel',
    product_count: 320,
    children: [
      {
        id: categoryIds.tops,
        code: 'APRL-TOPS',
        name: 'Tops',
        level: 1,
        industry_sector: 'apparel',
        product_count: 150,
        children: [
          {
            id: categoryIds.tshirts,
            code: 'APRL-TOPS-TSHIRT',
            name: 'T-Shirts',
            level: 2,
            industry_sector: 'apparel',
            product_count: 80,
            children: [],
          },
          {
            id: categoryIds.shirts,
            code: 'APRL-TOPS-SHIRT',
            name: 'Dress Shirts',
            level: 2,
            industry_sector: 'apparel',
            product_count: 70,
            children: [],
          },
        ],
      },
      {
        id: categoryIds.bottoms,
        code: 'APRL-BOTTOM',
        name: 'Bottoms',
        level: 1,
        industry_sector: 'apparel',
        product_count: 120,
        children: [
          {
            id: categoryIds.jeans,
            code: 'APRL-BOTTOM-JEAN',
            name: 'Jeans',
            level: 2,
            industry_sector: 'apparel',
            product_count: 60,
            children: [],
          },
          {
            id: categoryIds.pants,
            code: 'APRL-BOTTOM-PANT',
            name: 'Pants',
            level: 2,
            industry_sector: 'apparel',
            product_count: 60,
            children: [],
          },
        ],
      },
      {
        id: categoryIds.outerwear,
        code: 'APRL-OUTER',
        name: 'Outerwear',
        level: 1,
        industry_sector: 'apparel',
        product_count: 50,
        children: [],
      },
    ],
  },
  // Automotive
  {
    id: categoryIds.automotive,
    code: 'AUTO',
    name: 'Automotive',
    level: 0,
    industry_sector: 'automotive',
    product_count: 280,
    children: [
      {
        id: categoryIds.vehicles,
        code: 'AUTO-VEH',
        name: 'Vehicles',
        level: 1,
        industry_sector: 'automotive',
        product_count: 100,
        children: [],
      },
      {
        id: categoryIds.parts,
        code: 'AUTO-PARTS',
        name: 'Parts & Components',
        level: 1,
        industry_sector: 'automotive',
        product_count: 180,
        children: [
          {
            id: categoryIds.batteries,
            code: 'AUTO-PARTS-BATT',
            name: 'Batteries',
            level: 2,
            industry_sector: 'automotive',
            product_count: 50,
            children: [],
          },
          {
            id: categoryIds.tires,
            code: 'AUTO-PARTS-TIRE',
            name: 'Tires',
            level: 2,
            industry_sector: 'automotive',
            product_count: 40,
            children: [],
          },
        ],
      },
    ],
  },
  // Construction
  {
    id: categoryIds.construction,
    code: 'CONST',
    name: 'Construction',
    level: 0,
    industry_sector: 'construction',
    product_count: 200,
    children: [
      {
        id: categoryIds.materials,
        code: 'CONST-MAT',
        name: 'Building Materials',
        level: 1,
        industry_sector: 'construction',
        product_count: 200,
        children: [
          {
            id: categoryIds.steel,
            code: 'CONST-MAT-STEEL',
            name: 'Steel Products',
            level: 2,
            industry_sector: 'construction',
            product_count: 80,
            children: [],
          },
          {
            id: categoryIds.concrete,
            code: 'CONST-MAT-CONC',
            name: 'Concrete Products',
            level: 2,
            industry_sector: 'construction',
            product_count: 70,
            children: [],
          },
          {
            id: categoryIds.wood,
            code: 'CONST-MAT-WOOD',
            name: 'Wood Products',
            level: 2,
            industry_sector: 'construction',
            product_count: 50,
            children: [],
          },
        ],
      },
    ],
  },
  // Food & Beverage
  {
    id: categoryIds.foodBeverage,
    code: 'FOOD',
    name: 'Food & Beverage',
    level: 0,
    industry_sector: 'food_beverage',
    product_count: 180,
    children: [
      {
        id: categoryIds.beverages,
        code: 'FOOD-BEV',
        name: 'Beverages',
        level: 1,
        industry_sector: 'food_beverage',
        product_count: 80,
        children: [],
      },
      {
        id: categoryIds.packaged,
        code: 'FOOD-PKG',
        name: 'Packaged Foods',
        level: 1,
        industry_sector: 'food_beverage',
        product_count: 100,
        children: [],
      },
    ],
  },
  // Chemicals
  {
    id: categoryIds.chemicals,
    code: 'CHEM',
    name: 'Chemicals',
    level: 0,
    industry_sector: 'chemicals',
    product_count: 150,
    children: [
      {
        id: categoryIds.industrial,
        code: 'CHEM-IND',
        name: 'Industrial Chemicals',
        level: 1,
        industry_sector: 'chemicals',
        product_count: 100,
        children: [],
      },
      {
        id: categoryIds.specialty,
        code: 'CHEM-SPEC',
        name: 'Specialty Chemicals',
        level: 1,
        industry_sector: 'chemicals',
        product_count: 50,
        children: [],
      },
    ],
  },
  // Machinery
  {
    id: categoryIds.machinery,
    code: 'MACH',
    name: 'Machinery',
    level: 0,
    industry_sector: 'machinery',
    product_count: 120,
    children: [
      {
        id: categoryIds.industrial_eq,
        code: 'MACH-IND',
        name: 'Industrial Equipment',
        level: 1,
        industry_sector: 'machinery',
        product_count: 70,
        children: [],
      },
      {
        id: categoryIds.precision,
        code: 'MACH-PREC',
        name: 'Precision Machinery',
        level: 1,
        industry_sector: 'machinery',
        product_count: 50,
        children: [],
      },
    ],
  },
];

// Export category IDs for reference in other mock files
export { categoryIds };

// Helper function to count total categories (including nested)
export function countCategories(categories: MockCategory[]): number {
  return categories.reduce((count, cat) => {
    return count + 1 + countCategories(cat.children);
  }, 0);
}

// Helper function to get max depth
export function getMaxDepth(categories: MockCategory[], currentDepth = 0): number {
  if (categories.length === 0) return currentDepth;
  return Math.max(
    ...categories.map((cat) => getMaxDepth(cat.children, currentDepth + 1))
  );
}

// Helper function to filter categories by industry
export function filterByIndustry(
  categories: MockCategory[],
  industry: string
): MockCategory[] {
  return categories
    .filter((cat) => cat.industry_sector === industry)
    .map((cat) => ({
      ...cat,
      children: filterByIndustry(cat.children, industry),
    }));
}

// Helper function to limit depth
export function limitDepth(
  categories: MockCategory[],
  maxDepth: number,
  currentDepth = 0
): MockCategory[] {
  if (currentDepth >= maxDepth) {
    return categories.map((cat) => ({ ...cat, children: [] }));
  }
  return categories.map((cat) => ({
    ...cat,
    children: limitDepth(cat.children, maxDepth, currentDepth + 1),
  }));
}

// Flat list of all categories for product assignment
export function getAllCategoriesFlat(): MockCategory[] {
  const result: MockCategory[] = [];
  function flatten(categories: MockCategory[]) {
    for (const cat of categories) {
      result.push(cat);
      flatten(cat.children);
    }
  }
  flatten(mockCategories);
  return result;
}
