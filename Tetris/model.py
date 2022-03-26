class Block:
    def __init__(self, elements, center_index, color):
        self.elements = elements
        self.center_index = center_index
        self.is_falling = True
        self.color = color

    def remove(self, element):
        self.elements.remove(element)

    def rotate_preview(self):
        c_x = self.elements[self.center_index][0]
        c_y = self.elements[self.center_index][1]
        new_elements = []
        for element in self.elements:
            diff = [element[0] - c_x, element[1] - c_y]
            diff_p = [diff[1], -diff[0]]
            new = [diff_p[0] + c_x, diff_p[1] + c_y]
            new_elements.append(new)

        return new_elements

    def rotate(self):
        self.elements = self.rotate_preview()

    def drop_preview(self):
        return [[element[0] + 1, element[1]] for element in self.elements]

    def drop(self):
        self.elements = self.drop_preview()

    def move_left_preview(self):
        return [[element[0], element[1] - 1] for element in self.elements]

    def move_left(self):
        self.elements = self.move_left_preview()

    def move_right_preview(self):
        return [[element[0], element[1] + 1] for element in self.elements]

    def move_right(self):
        self.elements = self.move_right_preview()

    def drop_element_preview(self, element):
        return [element[0] + 1, element[1]]

    def drop_element(self, element):
        self.elements[self.elements.index(element)] = self.drop_element_preview(element)

    def __str__(self):
        return str(self.elements) + ", " + str(self.is_falling)


class IBlock(Block):
    def __init__(self):
        elements = [[0, 3], [0, 4], [0, 5], [0, 6]]
        center_index = 2
        super().__init__(elements, center_index, (0, 0, 255))


class JBlock(Block):
    def __init__(self):
        elements = [[0, 3], [0, 4], [0, 5], [1, 5]]
        center_index = 1
        super().__init__(elements, center_index, (255, 0, 0))


class LBlock(Block):
    def __init__(self):
        elements = [[0, 3], [0, 4], [0, 5], [1, 3]]
        center_index = 1
        super().__init__(elements, center_index, (255, 165, 0))


class OBlock(Block):
    def __init__(self):
        elements = [[0, 4], [0, 5], [1, 4], [1, 5]]
        center_index = 1
        super().__init__(elements, center_index, (0, 255, 0))

    def rotate_preview(self):
        return self.elements


class SBlock(Block):
    def __init__(self):
        elements = [[0, 4], [0, 5], [1, 3], [1, 4]]
        center_index = 3
        super().__init__(elements, center_index, (255, 192, 203))


class TBlock(Block):
    def __init__(self):
        elements = [[0, 4], [1, 3], [1, 4], [1, 5]]
        center_index = 2
        super().__init__(elements, center_index, (255, 0, 255))


class ZBlock(Block):
    def __init__(self):
        elements = [[0, 3], [0, 4], [1, 4], [1, 5]]
        center_index = 1
        super().__init__(elements, center_index, (255, 255, 0))
