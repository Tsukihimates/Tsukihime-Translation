const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const path = require('path');

const stylesConfig = {
    plugins: [
        new MiniCssExtractPlugin()
    ],
    entry: './webpack/scss/main.scss',
    output: {
        path: path.resolve(__dirname, '_site/assets/css'),
    },
    module: {
        rules: [
            {
                test: /\.s[ac]ss$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    'sass-loader',
                ],
            },
            {
                test: /\.(woff2?|ttf|eot|svg|png|jpe?g|gif)$/,
                loader: 'file-loader'
            }
        ]
    }
};


module.exports = [stylesConfig];

