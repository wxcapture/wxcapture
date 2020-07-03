import cv2

def clahe(in_img):
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(in_img)

def do_clahe_img(img):
    b_chn, g_chn, r_chn = cv2.split(img)
    return cv2.merge((clahe(b_chn), clahe(g_chn), clahe(r_chn)))

inputs = ["test_rockface.jpg"]

# To over-write, leave empty
output = "clahe_"

for img_path in inputs:
    print("Performing CLAHE on: \"" + img_path + "\"")

    out_img = do_clahe_img(cv2.imread(img_path))

    cv2.imwrite(output + img_path, out_img)

print("---DONE---")