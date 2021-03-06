
import pandas as pd
import numpy as np
from bokeh.io import output_file, show
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CustomJS, Range1d, Div

# read in data
df = pd.read_csv('./temp_nyc_2015.csv')

# get rid of leapday and duplicate cols
df.drop(59, 0, inplace=True)
df.drop(['Unnamed: 0', 'Unnamed: 0.1'], 1, inplace=True)
df['index'] = list(range(len(df)))
df.set_index('index', inplace=True)

# height and width of plot figures and divs
offs = round(50/450*800)
hw1 = 800
w2 = round(0.6 * hw1) + offs
h2 = round(w2 / 1.6)
w3 = w2
h3 = hw1 - h2 - offs//2


# angles for defining annular wedge position
# as well as start and end
full_angle = 2*np.pi

offset_angle = full_angle/4
day_angle = full_angle/len(df)

quarters = offset_angle * np.array(range(4))
months = offset_angle/3 * np.array(range(12))

day_starts = offset_angle - (df.index.to_series()+1) * day_angle
day_ends = offset_angle - df.index.to_series() * day_angle

# defining scale for radial plot
plot_range = [-450, 450]

max_radius = 400
min_radius = 100

max_temp = 120
min_temp = -20

a = (max_radius - min_radius) / (max_temp - min_temp)
b = min_radius - a * min_temp

def scale(temp):
    'scales temperature value to our radius range'
    return a * temp + b

# values for ticks and labels
temps = [0, 25, 50, 75, 100]

temp_tick = scale(np.array(temps))
temp_label = [str(x) + '°' for x in temps]

month_tick_x = [0, scale(100)+20, 0, -scale(100)-20]
month_tick_y = [scale(100)+20, -10, -scale(100)-40, -10]

month_label = ['Jan', 'Apr', 'Jul', 'Oct']

# colors
color = [
    '#0168a8', # rec hi/lo
    '#c5edc5', # avg hi/lo
    '#e07f4e', # 2015 hi/lo
]

bg_fill = 'white' # '#ffeee6'

alpha = 0.7

# selection wedge source data
selection_src = ColumnDataSource({
    'inner_radius': [scale(-10)],
    'outer_radius': [scale(120)],
    'start_angle': [offset_angle],
    'end_angle': [offset_angle - full_angle],
    'color': ['black'],
    'alpha': [0.01],
    'line_color': ['black'],
    'line_alpha': [alpha]
})

# Set up figure for radial plot, removing grid and border elements
p = figure(x_range=plot_range,
           y_range=plot_range,
           plot_height=hw1,
           plot_width=hw1,
           x_axis_type=None,
           y_axis_type=None,
           min_border=0,
           outline_line_color=bg_fill,
           border_fill_color=bg_fill,
           background_fill_color=bg_fill,
           tools='')

# annular wedges for record hi/lo, avg hi/lo and 2015 hi/lo
p.annular_wedge(0, 0,
                inner_radius=scale(df['recLow']),
                outer_radius=scale(df['recHigh']),
                start_angle=day_starts,
                end_angle=day_ends,
                color=color[0],
                line_color=None,
                alpha=alpha,
                legend='Record Hi/Lo')

p.annular_wedge(0, 0, 
                inner_radius=scale(df['avgLow']),
                outer_radius=scale(df['avgHigh']),
                start_angle=day_starts,
                end_angle=day_ends,
                color=color[1],
                line_color=None,
                alpha=alpha,
                legend='Average Hi/Lo')


p.annular_wedge(0, 0,
                inner_radius=scale(df['min']),
                outer_radius=scale(df['max']),
                start_angle=day_starts,
                end_angle=day_ends,
                color=color[2],
                line_color=None,
                alpha=alpha,
                legend='2015 Hi/Lo')

# add annular wedge for selection range
p.annular_wedge(0, 0,
                inner_radius='inner_radius',
                outer_radius='outer_radius',
                start_angle='start_angle',
                end_angle='end_angle',
                color='color',
                alpha='alpha',
                line_color='line_color',
                line_alpha='line_alpha',
                source=selection_src,
                legend='Selection')

# tick lines for months
p.annular_wedge(0, 0,
                inner_radius=temp_tick[0],
                outer_radius=temp_tick[-1],
                start_angle=months,
                end_angle=months,
                color=bg_fill)

# accented quarter marks
p.annular_wedge(0, 0,
                inner_radius=temp_tick[0],
                outer_radius=temp_tick[-1],
                start_angle=quarters,
                end_angle=quarters,
                color='lightgrey')

# temperature axis rings
p.annulus(0, 0,
          inner_radius=temp_tick,
          outer_radius=temp_tick,
          color='lightgrey')

# offset temperature labels, colored for contrast with plot
p.text(-temp_tick * np.cos(offset_angle/2), 
       temp_tick * np.sin(offset_angle/2),
       text=temp_label,
       angle=offset_angle/2,
       y_offset=np.linspace(-1,-5,5) * np.sin(offset_angle/2),
       x_offset=np.linspace(-1,-5,5) * np.cos(offset_angle/2),
       text_align='center',
       text_color=[
           'grey', 'white', 'white', 'grey', 'grey'
       ])

# quarterly month labels for reference
p.text(month_tick_x,
       month_tick_y,
       text=month_label,
       text_align='center',
       text_color='grey')

# chart title
p.text(0,
       415,
       text=['Annual Temperature - NYC 2015'],
       text_align='center',
       text_color='Black',
       text_font_size='20pt')

# format legend radial chart
p.legend.location = 'center'
p.legend.background_fill_alpha = 0.0
p.legend.border_line_alpha = 0.0

# remove toolbar + logo from radial chart
# interferes with layout
p.toolbar.logo = None
p.toolbar_location = None

# establishing day start end end datetime values, 
# for specifying left and right attributes of quad glyphs
df['dt'] = df['date'].apply(lambda d: pd.to_datetime(d + '-2015', format='%d-%b-%Y'))
df['left'] = df['dt']
df['right'] = df['dt'].shift(-1)
rcolix = list(df.columns).index('right')
df.iloc[-1, rcolix] = df['dt'].values[-1] + pd.Timedelta('1d')

# bound range for cartesian plot
# this will prevent user from scrolling/panning too far
range_start = df['left'].min()
range_end = df['right'].max()
ts_range = Range1d(start=range_start,
                   end=range_end,
                   bounds=(range_start, range_end))

# figure for cartesian time-series chart
# background color to match selection wedge -- subtle vis cue?
p2 = figure(x_axis_type='datetime',
            x_range=ts_range,
            plot_height=h2,
            plot_width=w2,
            min_border=0,
            outline_line_color=bg_fill,
            border_fill_color=bg_fill,
            background_fill_color='black',
            background_fill_alpha=0.01,
            tools='xpan,xwheel_zoom,reset',
            active_drag='xpan',
            active_scroll='xwheel_zoom')

# record hi/lo
p2.quad(top=df['recHigh'],
        bottom=df['recLow'],
        left=df['left'],
        right=df['right'],
        fill_color=color[0],
        fill_alpha=alpha,
        line_color=None)

# avg hi/lo
p2.quad(top=df['avgHigh'],
        bottom=df['avgLow'],
        left=df['left'],
        right=df['right'],
        fill_color=color[1],
        fill_alpha=alpha,
        line_color=None)

# 2015 hi/lo
p2.quad(top=df['min'],
        bottom=df['max'],
        left=df['left'],
        right=df['right'],
        fill_color=color[2],
        fill_alpha=alpha,
        line_color=None)

# syle plot grid to same color scheme as radial axis
p2.xgrid.grid_line_color = 'lightgrey'
p2.ygrid.grid_line_color = 'lightgrey'

# custom js callback code
# updates selection wedge based on range of dates
# displayed in cartesian chart
jscode='''
    function scale_date_to_radial(x){
        // name says it
        var full_angle = Math.PI * 2;
        var offset_angle = full_angle / 4;
        var day_angle = full_angle / 365;
    
        var date_offset = Date.parse('January 1, 2015');
        var day_value = 86400000;
        
        x = (x - date_offset)/day_value;
        x = offset_angle - (x * day_angle);
        
        return x
    };
    
    
    var data = source.data;
    var start = cb_obj.start; // cb_obj represents the model
    var end = cb_obj.end;     // bound to the callback..
    
    data['start_angle'] = [scale_date_to_radial(end)];
    data['end_angle'] = [scale_date_to_radial(start)];
    
    source.trigger('change');
'''
# bind callback to p2's x range and pass 
# selection wedge source to jscode
p2.x_range.callback = CustomJS(
    args=dict(source=selection_src), code=jscode
)

# empty div element for formatting
div1 = Div(text='', width=offs//4, height=h3-offs)

# promotional plug div, no shame
div2 = Div(text='''
    <p>
      <b>Linked Radial Chart</b>
      <br>
      by Tyler Nickerson 
    </p>
    <p> 
      This visualization aims to recreate the look and functionality of 
      Elija Meeks' 
      <a href='https://bl.ocks.org/emeeks/2fffa9abe50ac97603c7'>
        Brushable Radial Plot (in D3)
      </a>
      , using  
      <a href='http://bokeh.pydata.org/en/latest/'>
        Bokeh
      </a>. However, this layout reverses the positioning and relationship between the charts 
      to emphasize Bokeh's strengths. 
      
    </p>
    <p>
      The cartesian chart supports panning and scroll-to-zoom interactions;
      allowing the user to drill down into into the timeseries data. The range 
      of the cartesian chart is reflected in the 'selection' window of the radial chart 
      making at glance comparisons between the radial and cartesian chart 
      easier. The color selection was adjusted slightly to make it easier 
      for people with red-green colorblindness discern between the different
      fields.
    </p>
    <p>
      Evenutally, I would like to add the flexibility to update the cartesian
      chart range through interactions with the selection window. Support for
      these kinds of interactions are not yet developed in Bokeh. However, it
      may be possible by further extending the interactively using JavaScript.
    </p>
    <p>
      <a href='http://github.com/nmbrgts/Linked-Radial-Chart' target='_blank'>Source</a>    
      <a href='http://nmbrgts.github.io' taget='_blank'>Blog</a>    
      <a href='mailto:tylerjnickerson@gmail.com' target='_blank'>Email</a> 
    </p>''',
    height=h3-offs,
    width=w3-offs//2
)

# throw it all in a layout
layout = row(p, column(row(div1, div2), p2))

# designate output file and render our vis
output_file('linked_radial.html')
show(layout)
