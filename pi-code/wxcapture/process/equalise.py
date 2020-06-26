import os
import sys
import numpy as np
import cv2

def clahe(in_img):
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4)).apply(in_img)

def do_clahe_img(inp):
    b_chn, g_chn, r_chn = cv2.split(img)
    return cv2.merge((clahe(b_chn), clahe(g_chn), clahe(r_chn)))

inputs = [""]

output = "clahe_"

cnt = 0.0

for img_path in inputs:
    print("[" + str(round(cnt/len(inputs)*100)) + "%] Performing CLAHE on: \"" + img_path + "\"")
    cnt += 1

    img = cv2.imread(img_path)

    img = do_clahe(img)

    cv2.imwrite(output + img_path, out_img)

print("---DONE---")