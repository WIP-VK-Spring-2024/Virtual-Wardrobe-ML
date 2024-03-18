import cv2
import numpy as np
import json

from app.pkg.settings import settings

from app.pkg.ml.try_on.preprocessing.openpose.src import model
from app.pkg.ml.try_on.preprocessing.openpose.src import util
from app.pkg.ml.try_on.preprocessing.openpose.src.body import Body
from app.pkg.ml.try_on.preprocessing.openpose.src.hand import Hand

class PoseEstimation:

    def __init__(self):
        self.WEIGHTS_PATH = f"{settings.ML.WEIGHTS_PATH}/body_pose_model.pth" # f"/usr/src/app/app/pkg/ml/weights/body_pose_model.pth"
        self.body_estimation = Body(self.WEIGHTS_PATH)

    def __call__(self, input_path, key_point_output_path, output_path,):
        """
        input_path - path to resized image (to load)
        keypoint_output_path - path to json (to save)
        output_path - path to img (to save)
        
        """
        image = cv2.imread(input_path)
        if image is None:
            raise Exception(f"Image {input_path} is not found for pose estimation")
        assert image.shape == (512, 384, 3)

        candidate, subset = self.body_estimation(image)
        canvas = util.draw_bodypose(np.zeros_like(image), candidate, subset)
        arr = candidate.tolist()
        vals = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0]
        for i in range(0,18):
            if len(arr)==i or arr[i][3] != vals[i]:
                arr.insert(i,[-1,-1,-1,vals[i]])

        keypoints = {'keypoints':arr[:18]}
        cv2.imwrite(output_path,canvas)
        with open(key_point_output_path , 'w') as fin:
            fin.write(json.dumps(keypoints))

if __name__ == '__main__':
    pe = PoseEstimation()
    pe(
       "/usr/src/app/volume/data/resized/resized_human.png",
       "/usr/src/app/volume/data/pose/keypoints.json",
       "/usr/src/app/volume/data/pose/posed_human.png",
       )
# python3 -m app.pkg.ml.try_on.preprocessing.pose 
