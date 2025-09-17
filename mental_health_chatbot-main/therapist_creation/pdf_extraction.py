import os
import pdfplumber
import numpy as np
import cv2
from scipy import stats

class RobustPDFExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.pdf = pdfplumber.open(file_path)
        self.total_pages = len(self.pdf.pages)

    def __del__(self):
        if hasattr(self, 'pdf') and self.pdf:
            self.pdf.close()

    def _get_valid_bbox(self, page):
        """Get safe bounding box coordinates"""
        return (
            max(page.cropbox[0], 0),
            max(page.cropbox[1], 0),
            min(page.cropbox[2], page.width),
            min(page.cropbox[3], page.height)
        )

    def _detect_columns(self, page):
        """Improved column detection with statistical validation"""
        try:
            # Method 1: Visual line detection with mode validation
            img = page.to_image(resolution=150).original.convert('L')
            edges = cv2.Canny(np.array(img), 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/720, 100,
                                   minLineLength=int(page.height*0.7),
                                   maxLineGap=2)
            verts = []
            if lines:
                verts = [l[0][0] for l in lines 
                         if abs(l[0][0]-l[0][2]) < 5 and 
                         (0.3*page.width < l[0][0] < 0.7*page.width)]
                if verts:
                    mode_x = stats.mode(np.round(verts, -1)).mode[0]
                    if 0.3*page.width < mode_x < 0.7*page.width:
                        return mode_x

            # Method 2: Text gap analysis with density check
            words = page.extract_words()
            if len(words) > 15:
                x_coords = sorted([w['x0'] for w in words] + [w['x1'] for w in words])
                gaps = [(x_coords[i] - x_coords[i-1], x_coords[i-1]) 
                       for i in range(1, len(x_coords))]
                
                # Dynamic gap threshold (20% width) with density validation
                valid_gaps = [g for g in gaps 
                             if g[0] > page.width*0.2 and 
                             (0.3*page.width < g[1] < 0.7*page.width)]
                
                if valid_gaps:
                    best_gap = max(valid_gaps, key=lambda x: x[0])
                    split_x = best_gap[1] + best_gap[0]/2
                    # Validate split position
                    left_density = len([w for w in words if w['x1'] < split_x])
                    right_density = len([w for w in words if w['x0'] > split_x])
                    if abs(left_density - right_density)/(left_density + right_density) < 0.3:
                        return split_x

            return None
        except Exception as e:
            print(f"Detection error: {str(e)}")
            return None

    def _safe_crop(self, page, bbox):
        """Safe cropping with bounds checking"""
        x0, y0, x1, y1 = (
            max(bbox[0], page.bbox[0]),
            max(bbox[1], page.bbox[1]),
            min(bbox[2], page.bbox[2]),
            min(bbox[3], page.bbox[3])
        )
        return page.crop((x0, y0, x1, y1))

    def process_page(self, page_num):
        """Robust page processing with error handling"""
        try:
            page = self.pdf.pages[page_num]
            valid_bbox = self._get_valid_bbox(page)
            base_page = page.within_bbox(valid_bbox)
            
            split_x = self._detect_columns(base_page)
            cols = 1  # Default column count
            
            if split_x and (0.3*base_page.width < split_x < 0.7*base_page.width):
                try:
                    # Extract with protected buffer zones
                    left = self._safe_crop(base_page, (0, 0, split_x-15, base_page.height)).extract_text(layout=True, x_tolerance=1.5)
                    right = self._safe_crop(base_page, (split_x+15, 0, base_page.width, base_page.height)).extract_text(layout=True, x_tolerance=1.5)
                    return f"{left}\n\n{right}", 2
                except:
                    cols = 1  # Fallback if extraction fails
                    
            # Fallback to full page extraction
            text = base_page.extract_text(
                layout=True, 
                x_tolerance=2,
                y_tolerance=1,
                use_text_flow=True
            )
            return text.strip() or "CONTENT_NOT_EXTRACTED", cols
            
        except Exception as e:
            return f"PAGE_EXTRACTION_ERROR: {str(e)}", 0

def extract_pdf(input_path, output_path):
    extractor = RobustPDFExtractor(input_path)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i in range(extractor.total_pages):
                text, cols = extractor.process_page(i)
                f.write(f"=== Page {i+1} ({cols} cols) ===\n{text}\n\n")
        print(f"Extraction complete: {output_path}")
    finally:
        if hasattr(extractor, 'pdf'):
            extractor.pdf.close()


if __name__ == "__main__":
    folder_path = "/Users/mac/Documents/mental_engine_chatbot/therapist_creation/books"
    output_dir  = "/Users/mac/Documents/mental_engine_chatbot/therapist_creation/extracted_books"
    os.makedirs(output_dir, exist_ok=True)    # ensure the output folder exists

    for fname in os.listdir(folder_path):
        # only process actual PDF files
        if not fname.lower().endswith(".pdf"):
            continue

        PDF_PATH = os.path.join(folder_path, fname)
        pdf_name = os.path.splitext(fname)[0]
        OUTPUT_PATH = os.path.join(output_dir, f"{pdf_name}.txt")

        extract_pdf(PDF_PATH, OUTPUT_PATH)
    



