// Comparison PNG Export - Clientside callback
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.comparison = window.dash_clientside.comparison || {};
window.dash_clientside.comparison.export_png = function(trigger_data) {
            if (!trigger_data || !trigger_data.group) {
                return window.dash_clientside.no_update;
            }

            const group = trigger_data.group;
            console.log('[PNG Export] Exporting group:', group);

            const rowId = 'comparison-heatmap-row-' + group;
            const colorbarId = 'comparison-colorbar-' + group;

            const rowEl = document.getElementById(rowId);
            const colorbarContainer = document.getElementById(colorbarId);

            console.log('[PNG Export] Found rowEl:', !!rowEl, 'colorbarContainer:', !!colorbarContainer);

            if (!rowEl) {
                console.error('[PNG Export] ERROR: rowEl not found with ID:', rowId);
                return window.dash_clientside.no_update;
            }

            if (!colorbarContainer) {
                console.error('[PNG Export] ERROR: colorbarContainer not found with ID:', colorbarId);
                return window.dash_clientside.no_update;
            }

            if (!window.Plotly || !Plotly.toImage) {
                console.error('[PNG Export] ERROR: Plotly not available');
                return window.dash_clientside.no_update;
            }

            const heatmapContainers = Array.prototype.slice.call(
                rowEl.getElementsByClassName("comparison-heatmap-graph")
            );

            if (!heatmapContainers.length) {
                console.error('[PNG Export] ERROR: No heatmap containers found');
                return window.dash_clientside.no_update;
            }

            const heatmapPlots = heatmapContainers.map(function(container) {
                return container.getElementsByClassName("js-plotly-plot")[0] || container;
            });
            const colorbarPlot = colorbarContainer.getElementsByClassName("js-plotly-plot")[0] || colorbarContainer;

            const loadImage = function(src) {
                return new Promise(function(resolve, reject) {
                    const img = new Image();
                    img.onload = function() { resolve(img); };
                    img.onerror = reject;
                    img.src = src;
                });
            };

            const exportScale = 4;  // Higher resolution for better quality (4x)
            const gap = 14 * exportScale;
            const padding = 12 * exportScale;
            const logoCardWidth = 70 * exportScale;

            const heatmapDims = heatmapPlots.map(function(plot) {
                const layout = plot._fullLayout || {};
                return {
                    width: Math.round(layout.width || plot.clientWidth || 600),
                    height: Math.round(layout.height || plot.clientHeight || 380)
                };
            });
            const colorbarLayout = colorbarPlot._fullLayout || {};
            const colorbarWidth = Math.round(colorbarLayout.width || colorbarPlot.clientWidth || 90);
            const colorbarHeight = Math.round(colorbarLayout.height || colorbarPlot.clientHeight || heatmapDims[0].height);

            (async () => {
                try {
                    const heatmapUrls = await Promise.all(
                        heatmapPlots.map(function(plot, idx) {
                            return Plotly.toImage(plot, {
                                format: 'png',
                                width: heatmapDims[idx].width,
                                height: heatmapDims[idx].height,
                                scale: exportScale
                            });
                        })
                    );
                    const colorbarUrl = await Plotly.toImage(colorbarPlot, {
                        format: 'png',
                        width: colorbarWidth,
                        height: colorbarHeight,
                        scale: exportScale
                    });

                    const heatmapImgs = await Promise.all(heatmapUrls.map(loadImage));
                    const colorbarImg = await loadImage(colorbarUrl);
                    const logoImg = await loadImage("/assets/OP_Logo.png");

                    const totalHeatmapWidth = heatmapImgs.reduce(function(sum, img) { return sum + img.width; }, 0);
                    const maxHeatmapHeight = heatmapImgs.reduce(function(max, img) { return Math.max(max, img.height); }, 0);

                    const canvasWidth = padding * 2 + logoCardWidth + gap + totalHeatmapWidth + gap * (heatmapImgs.length - 1) + gap + colorbarImg.width;
                    const canvasHeight = padding * 2 + Math.max(maxHeatmapHeight, colorbarImg.height);

                    const canvas = document.createElement('canvas');
                    canvas.width = canvasWidth;
                    canvas.height = canvasHeight;
                    const ctx2d = canvas.getContext('2d');

                    ctx2d.fillStyle = '#ffffff';
                    ctx2d.fillRect(0, 0, canvasWidth, canvasHeight);

                    let cursorX = padding + logoCardWidth + gap;
                    const cursorY = padding;
                    heatmapImgs.forEach(function(img) {
                        ctx2d.drawImage(img, cursorX, cursorY);
                        cursorX += img.width + gap;
                    });

                    ctx2d.drawImage(colorbarImg, cursorX, padding);

                    const logoTargetWidth = logoCardWidth * 0.5;
                    const logoScale = logoTargetWidth / logoImg.width;
                    const logoTargetHeight = logoImg.height * logoScale;
                    const logoX = padding + logoCardWidth - logoTargetWidth;
                    const logoY = padding + maxHeatmapHeight - logoTargetHeight - 6 * exportScale;
                    ctx2d.drawImage(logoImg, logoX, logoY, logoTargetWidth, logoTargetHeight);

                    const link = document.createElement('a');
                    link.href = canvas.toDataURL('image/png');
                    link.download = 'comparison_' + group + '.png';
                    link.click();
                } catch (err) {
                    console.error('[PNG Export] Export failed:', err);
                }
            })();

            return window.dash_clientside.no_update;
        };
