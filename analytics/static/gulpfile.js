var gulp = require('gulp');
var jshint = require('gulp-jshint');
var bower = require('gulp-bower');
var bowerMainFiles = require('main-bower-files');
var jscs = require('gulp-jscs');
var lintspaces = require('gulp-lintspaces');

gulp.task('lint', function() {
    return gulp.src('js/*.js')
        .pipe(jshint({
            eqeqeq: false,
            browser: true,
            bitwise: true,
            laxbreak: true,
            newcap: false,
            undef: true,
            unused: true,
            predef: ['requirejs', 'require', 'define', 'app', '$'],
            strict: true,
            lastsemic: true,
            scripturl: true,
            "-W041": false
        }))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jscs({
            requireParenthesesAroundIIFE: true,
            requireSpaceAfterKeywords: ['do', 'for', 'if', 'else', 'switch', 'case', 'try', 'while', 'return', 'typeof'],
            requireSpaceBeforeBlockStatements: true,
            requireSpacesInConditionalExpression: true,
            requireSpacesInFunction: {beforeOpeningCurlyBrace: true},
            disallowSpacesInFunction: {beforeOpeningRoundBrace: true},
            requireBlocksOnNewline: 1,
            disallowPaddingNewlinesInBlocks: true,
            disallowEmptyBlocks: true,
            disallowSpacesInsideObjectBrackets: 'all',
            disallowSpacesInsideArrayBrackets: 'all',
            disallowSpacesInsideParentheses: true,
            disallowQuotedKeysInObjects: true,
            disallowSpaceAfterObjectKeys: true,
            requireSpaceBeforeObjectValues: true,
            requireCommaBeforeLineBreak: true,
            requireOperatorBeforeLineBreak: true,
            disallowSpaceAfterPrefixUnaryOperators: true,
            disallowSpaceBeforePostfixUnaryOperators: true,
            requireSpaceBeforeBinaryOperators: true,
            requireSpaceAfterBinaryOperators: true,
            disallowImplicitTypeConversion: ['numeric', 'string'],
            requireCamelCaseOrUpperCaseIdentifiers: 'ignoreProperties',
            disallowKeywords: ['with'],
            disallowMultipleLineStrings: true,
            disallowMultipleLineBreaks: true,
            disallowMixedSpacesAndTabs: true,
            disallowTrailingComma: true,
            disallowKeywordsOnNewLine: ['else'],
            requireCapitalizedConstructors: true,
            requireDotNotation: true,
            disallowYodaConditions: true,
            disallowNewlineBeforeBlockStatements: true,
            validateLineBreaks: 'LF',
            validateParameterSeparator: ', '
            }
        ))
        .pipe(lintspaces({
            styles: {
                options: {
                    showValid: true,
                    newline: true,
                    indentation: 'spaces',
                    spaces: 2,
                    newlineMaximum: 2,
                    trailingspaces: true,
                    ignores: ['js-comments']
                },
                src: [
                    'static/**/*.css'
                ]
            },
            javascript: {
                options: {
                    showValid: true,
                    newline: true,
                    indentation: 'spaces',
                    spaces: 4,
                    trailingspaces: true,
                    ignores: ['js-comments']
                },
                src: [
                    'static/**/*.js',
                    '!static/js/libs/**'
                ]
            }
        }));
});



gulp.task('bower-build', function() {
    return bower();
});

gulp.task('bower', ['bower-build'], function() {
    return gulp.src(bowerMainFiles({
           checkExistence: true
       })
    )
    .pipe(gulp.dest('js/libs/'));
});