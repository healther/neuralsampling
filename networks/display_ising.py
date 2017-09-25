import time
from itertools import islice

from matplotlib import animation
import matplotlib.pyplot as plt
plt.rcParams['animation.ffmpeg_path'] = u'/home/hd/hd_hd/hd_wv385/transfer/ffmpeg-3.3.4-64bit-static/ffmpeg'
import numpy as np


def plot_state(state, plotname='state.pdf'):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.imshow(state, interpolation='none')

    plt.savefig(plotname)
    plt.close()


def get_state(line):
    state = np.array([int(s) for s in line.strip()])

    n = len(state)
    linearsize = np.sqrt(n)
    if int(linearsize) != linearsize:
        raise ValueError("State of size {} found, expected a square. Aborting.".format(n))
    linearsize = int(linearsize)

    state = state.reshape(linearsize, linearsize)
    return state


def get_line(filename, timestep):
    with open(filename, 'r') as f:
        for i in range(timestep-1):
            f.next()
        line = f.readline()
    return line


def plot_timestep(filename, timestep):
    line = get_line(filename, timestep)
    plot_state(state, filename + '_{:05d}.pdf'.format(timestep))


def plot_timeseries(filename):
    with open(filename, 'r') as f:
        for i, line in enumerate(f):
            print(i)
            plot_state(get_state(line), plotname=filename+'_{:05d}.pdf'.format(i))


def animate(filename, from_timestep, to_timestep):
    f = open(filename, 'r')
    #with open(filename, 'r') as f:
    #    frames = [get_state(line.strip()) for line in f]
    for _ in range(4):
        line = f.readline()
    global i
    i = 0
    fig = plt.figure()
    ax = fig.add_subplot(111)
    im = ax.imshow(get_state(line.strip()), interpolation='none')
    lab_text = ax.text(0.5, 1.01, '', va='bottom', ha='right',
                           transform=ax.transAxes, color='green')
    def update(line):
        global i
        frame = get_state(line.strip())
        i += 1
        print(i)
        im.set_data(frame)
        lab_text.set_text('Timestep: {}'.format(i))
        return im, lab_text

    ani = animation.FuncAnimation(fig, update, frames=islice(f, 50, 1000000, 50), blit=True, interval=10., save_count=1000000)
    ani.save(filename + '.mp4', animation.writers['ffmpeg']())

def anitest():
    def update_line(num, data, line):
        line.set_data(data[..., :num])
        return line,

    # Set up formatting for the movie files
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)


    fig1 = plt.figure()

    data = np.random.rand(2, 25)
    l, = plt.plot([], [], 'r-')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel('x')
    plt.title('test')
    line_ani = animation.FuncAnimation(fig1, update_line, 25, fargs=(data, l),
                                                       interval=50, blit=True)
    line_ani.save('lines.mp4', writer='ffmpeg')
    print(line_ani.to_html5_video())

    fig2 = plt.figure()

    x = np.arange(-9, 10)
    y = np.arange(-9, 10).reshape(-1, 1)
    base = np.hypot(x, y)
    ims = []
    for add in np.arange(15):
        ims.append((plt.pcolor(x, y, base + add, norm=plt.Normalize(0, 30)),))

    im_ani = animation.ArtistAnimation(fig2, ims, interval=50, repeat_delay=3000,
                                                               blit=True)
    im_ani.save('im.mp4', writer=writer)

if __name__ == "__main__":
    import sys
    if len(sys.argv)==2:
        plot_timeseries(filename=sys.argv[1])
    elif len(sys.argv)==3:
        plot_timestep(filename=sys.argv[1], timestep=int(sys.argv[2]))
    elif len(sys.argv)==4:
        animate(filename=sys.argv[1], from_timestep=int(sys.argv[2]), to_timestep=int(sys.argv[3]))

