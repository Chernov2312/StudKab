import { spawnSync } from 'node:child_process'

const openAdvisory = 'https://github.com/advisories/GHSA-fc5q-39xc-vjpf'
const npm = process.env.npm_execpath
if (!npm) throw new Error('Run this check with npm run audit.')

const run = spawnSync(process.execPath, [npm, 'audit', '--json'], { encoding: 'utf8' })
if (run.error) throw run.error

const report = JSON.parse(run.stdout)
if (!report.vulnerabilities || run.status === null || run.status > 1) {
  throw new Error('The npm advisory service did not return a vulnerability report.')
}

const advisories = Object.values(report.vulnerabilities).flatMap(entry =>
  entry.via.filter(item => typeof item === 'object'),
)
const unexpected = advisories.filter(item => item.url !== openAdvisory || item.name !== 'picomatch')
if (unexpected.length) {
  for (const item of unexpected) console.error(item.name, item.severity, item.url)
  process.exitCode = 1
} else if (advisories.length) {
  console.warn('Open build-time advisory for picomatch:', openAdvisory)
} else {
  console.log('No known npm development advisories.')
}
