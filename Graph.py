# Graph.py

from statistics import mean
from matplotlib import gridspec
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, FuncFormatter
import randomcolor
from Utils import format_bps

class Graph:
    def __init__(self, base_stations, clients, xlim, map_limits,
                 output_dpi=500, scatter_size=15, output_filename='output.png'):
        self.output_filename = output_filename
        self.base_stations = base_stations
        self.clients = clients
        self.xlim = xlim
        self.map_limits = map_limits
        self.output_dpi = output_dpi
        self.scatter_size = scatter_size
        self.fig = plt.figure(figsize=(16,9))
        self.fig.canvas.manager.set_window_title('Network Slicing Simulation')
        self.gs = gridspec.GridSpec(4, 3, width_ratios=[6, 3, 3])

        rand_color = randomcolor.RandomColor()
        colors = rand_color.generate(luminosity='bright', count=len(base_stations))
        # colors = [np.random.randint(256*0.2, 256*0.7+1, size=(3,))/256 for __ in range(len(self.base_stations))]
        for c, bs in zip(colors, self.base_stations):
            bs.color = c

    def draw_live(self, *stats):
        ani = animation.FuncAnimation(self.fig, self.draw_all, fargs=stats, interval=1000)
        plt.show()

    def draw_all(self, *stats):
        plt.clf()
        self.draw_map()
        self.draw_stats(*stats)

    def draw_map(self):
        markers = ['o', 's', 'p', 'P', '*', 'H', 'X', 'D', 'v', '^', '<', '>', '1', '2', '3', '4']
        self.ax = plt.subplot(self.gs[:, 0])
        xlims, ylims = self.map_limits
        self.ax.set_xlim(xlims)
        self.ax.set_ylim(ylims)
        self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
        self.ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
        self.ax.set_aspect('equal')
        
        # base stations
        for bs in self.base_stations:
            circle = plt.Circle(bs.coverage.center, bs.coverage.radius,
                                fill=False, linewidth=2, alpha=0.9, color=bs.color)
            self.ax.add_artist(circle)
        
        # clients
        legend_indexed = []
        for c in self.clients:
            label = None
            if c.subscribed_slice_index not in legend_indexed and c.base_station is not None:
                label = c.get_slice().name
                legend_indexed.append(c.subscribed_slice_index)
            self.ax.scatter(c.x, c.y,
                            color=c.base_station.color if c.base_station is not None else '0.8',
                            label=label, s=15,
                            marker=markers[c.subscribed_slice_index % len(markers)])

        box = self.ax.get_position()
        self.ax.set_position([box.x0 - box.width * 0.05, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        leg = self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                             shadow=True, ncol=5)

        for i in range(len(legend_indexed)):
            leg.legendHandles[i].set_color('k')

    def draw_stats(self, vals, vals1, vals2, vals3, vals5, anomalies, capacities):
        self.ax1 = plt.subplot(self.gs[0, 1])
        self.ax1.plot(vals)
        self.ax1.set_xlim(self.xlim)
        locs = self.ax1.get_xticks()
        locs[0] = self.xlim[0]
        locs[-1] = self.xlim[1]
        self.ax1.set_xticks(locs)
        self.ax1.use_sticky_edges = False
        self.ax1.set_title(f'Connected Clients Ratio')

        self.ax2 = plt.subplot(self.gs[1, 1])
        self.ax2.plot(vals1)
        self.ax2.set_xlim(self.xlim)
        self.ax2.set_xticks(locs)
        self.ax2.yaxis.set_major_formatter(FuncFormatter(format_bps))
        self.ax2.use_sticky_edges = False
        self.ax2.set_title('Total Bandwidth Usage')

        self.ax3 = plt.subplot(self.gs[0, 2])
        self.ax3.plot(vals3)
        self.ax3.set_xlim(self.xlim)
        self.ax3.set_xticks(locs)
        self.ax3.use_sticky_edges = False
        self.ax3.set_title('Client Count Ratio per Slice')

        self.ax5 = plt.subplot(self.gs[2, 1])
        self.ax5.plot(vals5, label='Block ratio')
        anomaly_indices = [i for i, a in enumerate(anomalies) if a == -1]
        self.ax5.scatter(anomaly_indices, [vals5[i] for i in anomaly_indices], color='red', label='Anomalies')
        self.ax5.set_xlim(self.xlim)
        self.ax5.set_xticks(locs)
        self.ax5.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        self.ax5.use_sticky_edges = False
        self.ax5.set_title('Block ratio')
        self.ax5.legend()

        self.ax6 = plt.subplot(self.gs[1, 2])
        for bs_id, capacity in capacities.items():
            self.ax6.plot(capacity, label=f'BS_{bs_id}')
        self.ax6.set_xlim(self.xlim)
        self.ax6.set_xticks(locs)
        self.ax6.use_sticky_edges = False
        self.ax6.set_title('Base Station Capacities')
        self.ax6.legend(loc='upper right', fontsize='small')

        self.ax8 = plt.subplot(self.gs[2, 2])
        row_labels = [
            'Initial number of clients',
            'Average connected clients',
            'Average bandwidth usage',
            'Average block ratio',
        ]
        l, r = self.xlim
        cell_text = [
            [f'{len(self.clients)}'],
            [f'{mean(vals[l:r]):.2f}'],
            [f'{format_bps(mean(vals1[l:r]), return_float=True)}'],
            [f'{mean(vals5[l:r]):.4f}']
        ]
        
        self.ax8.axis('off')
        self.ax8.axis('tight')
        self.ax8.tick_params(axis='x', which='major', pad=15)
        self.ax8.table(cellText=cell_text, rowLabels=row_labels, colWidths=[0.35, 0.2], loc='center right')

        plt.tight_layout()

    def save_fig(self):
        self.fig.savefig(self.output_filename, dpi=1000)

    def show_plot(self):
        plt.show()

    def get_map_limits(self):
        # deprecated
        x_min = min([bs.coverage.center[0]-bs.coverage.radius for bs in self.base_stations])
        x_max = max([bs.coverage.center[0]+bs.coverage.radius for bs in self.base_stations])
        y_min = min([bs.coverage.center[1]-bs.coverage.radius for bs in self.base_stations])
        y_max = max([bs.coverage.center[1]+bs.coverage.radius for bs in self.base_stations])

        return (x_min, x_max), (y_min, y_max)

    def plot_average_consume_time(self, clients, output_filename='average_consume_time.png'):
        import matplotlib.pyplot as plt

        # Filter clients with connected time > 0 and consume time > 0
        filtered_clients = [c for c in clients if c.total_connected_time > 0 and c.total_consume_time > 0]
        if not filtered_clients:
            print("No clients with valid connected and consume times.")
            return

        # Separate clients by slice type
        iot_clients = [c for c in filtered_clients if c.get_slice() and c.get_slice().name == "iot"]
        data_clients = [c for c in filtered_clients if c.get_slice() and c.get_slice().name == "data"]

        # Calculate average consume time
        iot_avg_consume_times = [c.total_consume_time / c.total_connected_time for c in iot_clients]
        data_avg_consume_times = [c.total_consume_time / c.total_connected_time for c in data_clients]

        # Plot
        plt.figure(figsize=(10, 6))
        if iot_clients:
            plt.plot([c.pk for c in iot_clients], iot_avg_consume_times, marker='o', color='blue', linestyle='-', label='IoT Slice')
        if data_clients:
            plt.plot([c.pk for c in data_clients], data_avg_consume_times, marker='x', color='green', linestyle='--', label='Data Slice')

        plt.xlabel('Client ID')
        plt.ylabel('Average Consume Time')
        plt.title('Average Consume Time by Slice Type')
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_filename)
        print(f"Average consume time plot saved as {output_filename}.")
