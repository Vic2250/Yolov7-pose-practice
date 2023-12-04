import sys
import yaml
import cv2
import numpy as np
import torch
from torchvision import transforms

sys.path.append('yolov7')

from yolov7.utils.datasets import letterbox
from yolov7.utils.general import non_max_suppression_kpt
from yolov7.utils.plots import output_to_keypoint, word_identify, plot_skeleton_kpts

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def load_model():
    # get the default model name
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    model_name = config['model']['name']

    # use the complete model path
    path = 'Model/' + model_name
    model = torch.load(path, map_location=device)['model']
    # Put in inference mode
    model.float().eval()

    if torch.cuda.is_available():
        model.to(device)
    return model


def run_inference(image, model):
    # Resize and pad image
    result = letterbox(image, 960, stride=64, auto=True)
    image = result[0]
    filling = result[2]
    # Apply transforms
    image = transforms.ToTensor()(image)
    if torch.cuda.is_available():
        image = image.to(device)
    # Turn image into batch
    image = image.unsqueeze(0)
    with torch.no_grad():
        output, _ = model(image)
    return output, image, filling


def draw_keypoints(output, image, last_x, last_y, last_confidence, last_text, model):
    output = non_max_suppression_kpt(output,
                                     0.25, # Confidence Threshold
                                     0.65, # IoU Threshold
                                     nc=model.yaml['nc'], # Number of Classes
                                     nkpt=model.yaml['nkpt'], # Number of Keypoints
                                     kpt_label=True)
    with torch.no_grad():
        output = output_to_keypoint(output)
    nimg = image[0].permute(1, 2, 0) * 255
    nimg = nimg.cpu().numpy().astype(np.uint8)
    nimg = cv2.cvtColor(nimg, cv2.COLOR_RGB2BGR)
    result = ''
    x = None
    y = None
    confidence = 0
    
    # 文字辨識(人的框選範圍太小會視為沒人)
    for idx in range(output.shape[0]):
        result, x, y, confidence = word_identify(nimg, output[idx, 2:6], last_x, last_y, last_confidence, last_text)
    
    # 如果有人，就將人的關節點及人的範圍畫上圖片
    if result != '':
        for idx in range(output.shape[0]):
            nimg = plot_skeleton_kpts(nimg, output[idx, 2:6], output[idx, 7:].T, 3)
        
    return nimg, result, x, y, confidence


# the complete detection function
def detection_image(image, last_x, last_y, last_confidence, last_text, model):
    output, detect_image, filling = run_inference(image, model)
    detect_image, number, x, y, confidence = draw_keypoints(output, detect_image, last_x, last_y, last_confidence, last_text, model)
    return detect_image, number, x, y, confidence, filling


def restore_image(image, filling, height, width):
    top, bottom = int(round(filling[1] - 0.1)), int(round(filling[1] + 0.1))
    left, right = int(round(filling[0] - 0.1)), int(round(filling[0] + 0.1))
    x1 = 0 + left
    x2 = image.shape[1] - right
    y1 = 0 + top
    y2 = image.shape[0] - bottom
    frame = image[y1:y2, x1:x2]
    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
    return frame