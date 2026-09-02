import assert from 'node:assert/strict'
import test from 'node:test'
import { buildClaimsQuery } from './claims.js'

test('buildClaimsQuery omits blank values and encodes filters', () => {
  const query = new URLSearchParams(buildClaimsQuery({
    search: 'CLM-28001',
    partner: 'Horizon Bank',
    status: '',
    cursor: null,
    limit: 25,
  }))
  assert.equal(query.get('search'), 'CLM-28001')
  assert.equal(query.get('partner'), 'Horizon Bank')
  assert.equal(query.get('limit'), '25')
  assert.equal(query.has('status'), false)
  assert.equal(query.has('cursor'), false)
})

test('buildClaimsQuery trims user input', () => {
  assert.equal(buildClaimsQuery({ search: '  FarmTrust  ' }), 'search=FarmTrust')
})
