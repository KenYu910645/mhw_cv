WORKING_LIST = [
        (30, 24, 'mine_10', 2),
        (30, 52, 'neck_point', -1), 
        (26, 55.5, 'mine_neck', 2),
        (26, 65, 'mid_11', -1),
        (16.5, 55, 'upper_vein', -1), 
        (23, 48, 'mine_bridge_right', 2),
        (16.5, 55, 'upper_vein', -1),
        (11, 62, 'mine_bridge_left', 2),
        (12.5, 76.0, 'lower_vein', -1),
        (19, 75, 'trail_11', 2),
        (41, 87, 'bone_11', 2),
        (26, 65, 'mid_11', -1),
        (30, 52, 'neck_point', -1),
        (51, 39, 'super_mine', 2),
        (58, 27, 'trail_10', 2),
        (61, 22, 'bone_10', 2),
        (68.5, 11, 'mine_cats', 2),
        (70, 8, 'trail_cats', 2),
        (69, -2, 'upper_vein', -1),
        (73, -6, 'lower_vein', -1),
        (70, -10, 'super_bone', 2),
        (73, -6, 'lower_vein', -1),
        (63, 2, 'upper_vein', -1),
        (56.5, 8, 'bone_tree', 2),
        (44, 6, 'avoid_deer_1', -1),
        (33, 11, 'avoid_deer_2', -1)]
THE_WAY_BACK = [(-25.5, 68, 'mid_home', -1),
                (-26.5, 59, 'upper_vein', -1),
                (-29, 52, 'lower_vein', -1),
                (-18, 49, 'transition', -1),
                (3, 24, 'entry_point', -1),
                (28, 9, 'mid_4', -1),
                (51, 18 ,'mid_10', -1)]

if __name__ == "__main__":
    import cv2

    cv2.imshow("img_map", img_map)
    cv2.waitKey(0)
