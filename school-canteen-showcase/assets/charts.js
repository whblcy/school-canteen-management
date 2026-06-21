(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var green = style.getPropertyValue('--green').trim();

  // --- Chart: Monthly Finance Trend ---
  var chartFinance = echarts.init(document.getElementById('chart-finance'), null, { renderer: 'svg' });
  chartFinance.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, backgroundColor: '#fff', borderColor: rule, textStyle: { color: ink, fontSize: 13 } },
    legend: { data: ['采购支出', '出库成本'], top: 0, textStyle: { color: muted, fontSize: 12 } },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '金额(元)',
      nameTextStyle: { color: muted, fontSize: 11 },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLabel: { color: muted, fontSize: 11 }
    },
    series: [
      {
        name: '采购支出',
        type: 'bar',
        data: [18500, 16200, 19800, 22100, 20500, 23800, 25600, 24200, 21700, 19500, 20800, 27500],
        itemStyle: { color: accent, borderRadius: [4, 4, 0, 0] },
        barWidth: '35%'
      },
      {
        name: '出库成本',
        type: 'line',
        smooth: true,
        data: [15200, 14800, 17600, 19500, 18200, 21000, 22800, 21500, 19800, 17200, 18900, 24500],
        lineStyle: { color: accent2, width: 2.5 },
        itemStyle: { color: accent2 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: accent2 + '30' }, { offset: 1, color: accent2 + '05' }] } },
        symbol: 'circle', symbolSize: 6
      }
    ]
  });
  window.addEventListener('resize', function() { chartFinance.resize(); });

  // --- Chart: Category Distribution ---
  var chartCategory = echarts.init(document.getElementById('chart-category'), null, { renderer: 'svg' });
  chartCategory.setOption({
    animation: false,
    tooltip: { trigger: 'item', appendToBody: true, backgroundColor: '#fff', borderColor: rule, textStyle: { color: ink, fontSize: 13 }, formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 20, top: 'center', textStyle: { color: muted, fontSize: 12 }, itemWidth: 12, itemHeight: 12, itemGap: 12 },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: ink },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' }
      },
      data: [
        { value: 35, name: '蔬菜类', itemStyle: { color: '#34c759' } },
        { value: 28, name: '肉类', itemStyle: { color: '#ff3b30' } },
        { value: 18, name: '粮油类', itemStyle: { color: '#ff9500' } },
        { value: 15, name: '蛋类', itemStyle: { color: '#0071e3' } },
        { value: 12, name: '豆制品', itemStyle: { color: '#5856d6' } },
        { value: 10, name: '调味品', itemStyle: { color: '#af52de' } },
        { value: 8, name: '水产类', itemStyle: { color: '#30d158' } },
        { value: 6, name: '水果类', itemStyle: { color: '#64d2ff' } }
      ]
    }]
  });
  window.addEventListener('resize', function() { chartCategory.resize(); });
})();
