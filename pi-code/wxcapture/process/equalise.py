import os
import sys
import numpy as np
import cv2


def do_clahe(inp):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4)).apply(inp)
    return clahe

# if(len(sys.argv) == 1):
#     print("Error: No input files")
#     exit()

# inputs = sys.argv[1:]
# inputs = os.listdir()
inputs = [""]

output = "clahe_"

cnt = 0.0

for img_path in inputs:
    print("[" + str(round(cnt/len(inputs)*100)) + "%] Performing CLAHE on: \"" + img_path + "\"")
    cnt += 1

    img = cv2.imread(img_path)

    b_chn, g_chn, r_chn = cv2.split(img)

    b_chn, g_chn, r_chn = do_clahe(b_chn), do_clahe(g_chn), do_clahe(r_chn)

    out_img = cv2.merge((b_chn, g_chn, r_chn))

    cv2.imwrite(output + img_path, out_img)

print("---DONE---")