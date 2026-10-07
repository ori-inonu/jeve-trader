import {useEffect, useRef} from 'react';
import * as echarts from 'echarts/core';
import {LineChart, BarChart} from 'echarts/charts';
import {GridComponent, TooltipComponent, MarkLineComponent, DataZoomComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, MarkLineComponent, DataZoomComponent, CanvasRenderer]);

export function Chart({option, label='Gráfico'}:{option:echarts.EChartsCoreOption;label?:string}) {
  const element = useRef<HTMLDivElement>(null);
  const instance = useRef<echarts.EChartsType|null>(null);
  useEffect(() => {
    const chart = echarts.init(element.current!);
    instance.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(element.current!);
    return () => {observer.disconnect(); instance.current = null; chart.dispose();};
  }, []);
  useEffect(() => {
    instance.current?.setOption({...option, animation:!matchMedia('(prefers-reduced-motion: reduce)').matches, animationDurationUpdate:180});
  }, [option]);
  return <div ref={element} className="chart" role="img" aria-label={label}/>;
}
