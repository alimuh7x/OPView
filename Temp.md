
### 1. Figure & Margins
   - Margins: L=`50`, R=`50`, T=`50`, B=`50` px

### 2. Domain Fractions (margin / figure_size)
   - `x0 = 50/500     = 0.1000`
   - `x1 = 1 - 50/500 = 0.9000`
   - `y0 = 50/500     = 0.1000`
   - `y1 = 1 - 50/500 = 0.9000`

### 3. Available Plot Area (domain × figure_size)   - Figure Size: `500 x 500` px
   - Margins: L=`50`, R=`50`, T=`50`, B=`50` px

### 2. Domain Fractions (margin / figure_size)
   - `x0 = 50/500 = 0.1000`

   - Left Edge:   `x0 × 500 = 0.1000 × 500 = 50.0` px
   - Right Edge:  `x1 × 500 = 0.9000 × 500 = 450.0` px
   - Bottom Edge: `y0 × 500 = 0.1000 × 500 = 50.0` px
   - `x1 = 1 - 50/500 = 0.9000`
   - Top Edge:    `y1 × 500 = 0.9000 × 500 = 450.0` px
   - `y0 = 50/500 = 0.1000`
   - Width:  `450.0 - 50.0 = 400.0` px
   - `y1 = 1 - 50/500 = 0.9000`

### 3. Available Plot Area (domain × figure_size)
   - Height: `450.0 - 50.0 = 400.0` px

### 4. Aspect Ratios
   - Left Edge:   `x0 × 500 = 0.1000 × 500 = 50.0` px
   - Data Aspect (w/h):      `2.0000`
   - Plot Area Aspect (w/h): `1.0000`

### 5. Constraint Applied: **Data is WIDER**
   (Plot fills width, constrained in height)

   **Actual Dimensions:**
   - Actual Width:  `Available Width = 400.0` px
   - Actual Height: `Width / Data_Aspect`
                    `= 400.0 / 2.0000`
                    `= 200.0` px

   **Vertical Centering:**
   - Padding: `(Available_Height - Actual_Height) / 2`
              `= (400.0 - 200.0) / 2`
              `= 100.0` px
   - Actual Left:   `50.0` px (no horizontal padding)
   - Actual Bottom: `50.0 + 100.0 = 150.0` px

### 6. Final Actual Plot Position
   - Right Edge:  `x1 × 500 = 0.9000 × 500 = 450.0` px
   - Left:   `50.0` px
   - Bottom Edge: `y0 × 500 = 0.1000 × 500 = 50.0` px
   - Bottom: `150.0` px
   - Top Edge:    `y1 × 500 = 0.9000 × 500 = 450.0` px
   - Width:  `400.0` px
   - Width:  `450.0 - 50.0 = 400.0` px
   - Height: `200.0` px
   - Height: `450.0 - 50.0 = 400.0` px

### 7. Logo Positioning

   **Pixel Coordinates:**

### 4. Aspect Ratios   - Logo Size: `40` px
   - Logo X:    `5` px (fixed, 5px from left)

   - Logo Y:    `150.0` px (at actual plot bottom)

   **Convert to Paper Coordinates** (px / figure_size):   - Data Aspect (w/h):      `2.0000`
   - Plot Area Aspect (w/h): `1.0000`


### 5. Constraint Applied: **Data is WIDER**
   (Plot fills width, constrained in height)

   **Actual Dimensions:**
   - Actual Width:  `Available Width = 400.0` px
   - Actual Height: `Width / Data_Aspect`
                    `= 400.0 / 2.0000`
                    `= 200.0` px
   - Logo X (paper):    `5 / 500 = 0.0100`

   **Vertical Centering:**
   - Padding: `(Available_Height - Actual_Height) / 2`
   - Logo Y (paper):    `150.0 / 500 = 0.3000`
              `= (400.0 - 200.0) / 2`
              `= 100.0` px
   - Actual Left:   `50.0` px (no horizontal padding)
   - Logo Size (paper): `40 / 500 = 0.0800`

   **Anchoring:**   - Actual Bottom: `50.0 + 100.0 = 150.0` px

### 6. Final Actual Plot Position
   - Left:   `50.0` px
   - Bottom: `150.0` px
   - Width:  `400.0` px
   - Height: `200.0` px

### 7. Logo Positioning

   **Pixel Coordinates:**
   - Logo Size: `40` px
   - Logo X:    `5` px (fixed, 5px from left)

   - `xanchor='left'`, `yanchor='bottom'`
   - Logo Y:    `150.0` px (at actual plot bottom)

   **Convert to Paper Coordinates** (px / figure_size):
   - Logo bottom-left corner positioned at `(0.0100, 0.3000)`
======================================================================

   - Logo X (paper):    `5 / 500 = 0.0100`
   - Logo Y (paper):    `150.0 / 500 = 0.3000`
   - Logo Size (paper): `40 / 500 = 0.0800`

   **Anchoring:**
   - `xanchor='left'`, `yanchor='bottom'`
   - Logo bottom-left corner positioned at `(0.0100, 0.3000)`
======================================================================

data_width: 128.0, data_height: 64.0
