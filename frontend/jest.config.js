module.exports = {
  preset: '@vue/cli-plugin-unit-jest/presets/typescript-and-babel',
  "reporters": [
    "default",
    ["./node_modules/jest-html-reporter", {
      "pageTitle": "Testmaus"
    }]
  ]
}
