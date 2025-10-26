const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';

  return {
    entry: {
      // Main bundle for common functionality
      main: './app/static/js/main.js',

      // Page-specific bundles
      scores: './app/static/js/scores.js',
      games: './app/static/js/games.js',
      teams: './app/static/js/teams.js',
      tournament: './app/static/js/tournament.js',
      playground: './app/static/js/playground.js',
      'team-form': './app/static/js/team-form.js',

      // Shared utilities
      'modal-utils': './app/static/js/modal-utils.js',
      'websocket-client': './app/static/js/websocket-client.js',
    },

    output: {
      filename: '[name].[contenthash].js',
      path: path.resolve(__dirname, 'app/static/dist/js'),
      clean: true,
    },

    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [
                ['@babel/preset-env', {
                  targets: 'defaults',
                  modules: false,
                }]
              ],
            },
          },
        },
        {
          test: /\.css$/,
          use: [
            MiniCssExtractPlugin.loader,
            'css-loader',
            {
              loader: 'postcss-loader',
              options: {
                postcssOptions: {
                  plugins: [
                    'postcss-preset-env',
                  ],
                },
              },
            },
          ],
        },
      ],
    },

    plugins: [
      new MiniCssExtractPlugin({
        filename: '../css/[name].[contenthash].css',
      }),
    ],

    optimization: {
      minimize: isProduction,
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            compress: {
              drop_console: isProduction,
            },
          },
        }),
        new CssMinimizerPlugin(),
      ],
      splitChunks: {
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendor',
            chunks: 'all',
          },
        },
      },
    },

    devtool: isProduction ? 'source-map' : 'eval-source-map',

    stats: {
      colors: true,
      modules: false,
      children: false,
    },

    performance: {
      hints: isProduction ? 'warning' : false,
      maxEntrypointSize: 512000,
      maxAssetSize: 512000,
    },
  };
};
