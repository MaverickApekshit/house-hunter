/**
 * Rigorous TypeScript interface representing a property listing.
 * Exactly mirrors the backend PropertyResponse schema contract.
 */
export interface Property {
  id: number;
  title: string;
  price: number;                  // Standardized price field (rent)
  bhk: string;                    // Property configuration (e.g., "3 BHK")
  location: string;               // Localized property area (locality)
  url: string;                    // Anchor listing url
  latitude?: number;              // Geographical latitude coordinates
  longitude?: number;             // Geographical longitude coordinates
  commute_duration_mins?: number; // Commute duration to target destination
  status: 'New' | 'Pending' | 'Interested' | 'Contacted' | 'Rejected';
  created_at: string;             // Date and time listing was tracked
  source: string;                 // Source scraper/mode origin
  deposit: number;                // Calculated security deposit
  area_sqft?: number;             // Optional total area size in square feet
}
