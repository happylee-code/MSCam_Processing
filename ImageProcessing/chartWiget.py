import sys

import matplotlib
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication

matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from ImageProcessing.matplotlibBar import ToolBar

class MyCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):

        # 配置中文显示
        plt.rcParams['font.family'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

        self.fig = Figure(figsize=(width, height), dpi=dpi)  # 新建一个figure

        self.axes = self.fig.add_subplot(111)  # 建立一个子图，如果要建立复合图，可以在这里修改
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        # FigureCanvas.setSizePolicy(self,
        #                            QSizePolicy.Expanding,
        #                            QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def draw_figure(self,x,ys,colors):
        # x = [u'R', u'G', u'B']
        # y = [15,150,200]
        self.axes.clear()
        for i,y in enumerate(ys):
            self.axes.plot(x,y,marker=".",color=colors[i%(len(colors))])
        # self.axes.set_yticks(range(0, 2, 0.1))
        self.axes.grid(True)

        # self.axes.set_yticklabels(('a', 'b', 'c', 'd', 'e'))
        # self.axes.set_xticks(range(1, 6))
        # self.axes.set_xticklabels((u'R', u'G', u'B'))
        self.draw()
        self.fig.canvas.draw_idle()



class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)
        self.initUi()

    def initUi(self):
        layout = QVBoxLayout(self)
        self.mpl = MyCanvas(self, width=2, height=2, dpi=100)
        self.mpl.get_default_filename = lambda: 'new_default_name.png'
        self.mpl_tool = ToolBar(self.mpl,self) #添加完整工具栏
        self.mpl.draw_figure([u'R', u'G', u'B'],[[0.005,0.55200,0.300],[0.150,0.300,0.120]],["#800000", "#FF0000", "#C71585", "#4B0082", "#800080", "#6A5ACD", "#8B4513", "#D2691E", "#FF4500",
                      "#FF8C00", "#B8860B"])
        # 初始化显示甘特图
        layout.addWidget(self.mpl)
        layout.addWidget(self.mpl_tool)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MatplotlibWidget()
    sys.exit(app.exec_())
