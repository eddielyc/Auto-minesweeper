# -*- coding: utf-8 -*-
# Time    : 2023/1/4 19:19
# Author  : Yichen Lu
import time

from PIL import Image, ImageGrab
from pathlib import Path
import numpy as np
from resolver.key_points import *
from global_variables import *
from skimage.feature import hog


class Resolver(object):
    def __init__(self, front_side):
        self.front_side = front_side

        self.hints = dict()
        self.flag = None
        self.unseen = None

        self.win = None
        self.over = None

        self.src_features = self.load_src()

    def load_src(self, src_dir="src"):
        src_dir = Path(src_dir)
        src_features = []
        # FIXME: I cannot find '8' image...
        for i in range(8):
            src = Image.open(src_dir / f"{i}.png").resize((GRID_W_RES, GRID_H_RES))
            self.hints[str(i)] = self.normalize(
                self.extract_feature(self.center_crop(self.image_to_array(src)))
            )

            src_features.append(self.hints[str(i)])

        src = Image.open(src_dir / f"flag.png").resize((GRID_W_RES, GRID_H_RES))
        self.flag = self.normalize(
            self.extract_feature(self.center_crop(self.image_to_array(src)))
        )
        src_features.append(self.flag)

        src = Image.open(src_dir / f"unseen.png").resize((GRID_W_RES, GRID_H_RES))
        self.unseen = self.normalize(
            self.extract_feature(self.center_crop(self.image_to_array(src)))
        )
        src_features.append(self.unseen)

        src = Image.open(src_dir / f"win.png").resize((64, 30))
        self.win = self.normalize(
            self.extract_feature(self.center_crop(self.image_to_array(src), w=3))
        )[np.newaxis, ...]

        src = Image.open(src_dir / f"over.png").resize((64, 30))
        self.over = self.normalize(
            self.extract_feature(self.center_crop(self.image_to_array(src), w=3))
        )[np.newaxis, ...]

        return np.stack(src_features)

    @staticmethod
    def extract_feature(image):
        feature = hog(image, block_norm="L2-Hys", multichannel=True)
        # feature = image.flatten()
        return feature

    @staticmethod
    def gridify(board):
        grids = []
        for h in range(HEIGHT):
            row = []
            for w in range(WIDTH):
                top = int(BOARD_HEIGHT / HEIGHT * h)
                bottom = int(BOARD_HEIGHT / HEIGHT * (h + 1)) + 1
                left = int(BOARD_WIDTH / WIDTH * w)
                right = int(BOARD_WIDTH / WIDTH * (w + 1)) + 1
                row.append(np.array(Image.fromarray(board[top: bottom, left: right]).resize((GRID_W_RES, GRID_H_RES)),
                                    dtype=np.float))
            grids.append(row)
        return grids

    def classify(self, image):
        center_cropped = self.center_crop(image)
        feature = self.normalize(self.extract_feature(center_cropped))
        feature = feature[np.newaxis, ...]

        similarities = np.matmul(feature, self.src_features.T)
        argmax = similarities.flatten().argmax()
        if 0 <= argmax <= 7:
            return str(argmax)
        elif argmax == 8:
            return FLAG
        elif argmax == 9:
            return UNSEEN
        else:
            raise RuntimeError

    def center_crop(self, image, w=8):
        return image[w: -w, w: -w, ...]

    @staticmethod
    def normalize(feature):
        assert len(feature.shape) == 1
        return feature / np.linalg.norm(feature, ord=2)

    def resolve(self):
        board = ImageGrab.grab(bbox=(LEFT, TOP, RIGHT, BOTTOM))
        board = self.image_to_array(board)
        board = self.gridify(board)

        for i, row in enumerate(board):
            for j, grid in enumerate(row):
                board[i][j] = self.classify(grid)

        self.front_side.board = board

    def is_win_or_over(self):
        # call time.sleep() here because the win or over board cannot pop-up immediately
        time.sleep(0.05)
        board = ImageGrab.grab(bbox=(WIN_LEFT, WIN_TOP, WIN_RIGHT, WIN_BOTTOM))
        board = self.image_to_array(board)

        center_cropped = self.center_crop(board, w=3)
        feature = self.normalize(self.extract_feature(center_cropped))
        feature = feature[np.newaxis, ...]

        win_sim = np.matmul(feature, self.win.T).flatten()

        time.sleep(0.05)
        board = ImageGrab.grab(bbox=(OVER_LEFT, OVER_TOP, OVER_RIGHT, OVER_BOTTOM))
        board = self.image_to_array(board)

        center_cropped = self.center_crop(board, w=3)
        feature = self.normalize(self.extract_feature(center_cropped))
        feature = feature[np.newaxis, ...]

        over_sim = np.matmul(feature, self.over.T).flatten()

        if win_sim > over_sim and win_sim >= 0.7:
            return "WIN"
        elif over_sim > win_sim and over_sim >= 0.7:
            return "OVER"
        else:
            return "OK"

    def image_to_array(self, image):
        return np.array(image, dtype=np.uint8)[..., :3]
