const express = require('express');
const router = express.Router();

// Public "Meet the Team" staff directory, shown on the storefront's About page.
// Real company sites commonly publish a staff directory like this, and it's a
// realistic recon target: the work-email local part reveals the company's
// username convention (first initial + last name), the same OSINT step a red
// teamer would normally do against LinkedIn before a password-spray attempt.
// Only the 15 documented employees are listed here; the 12 hidden AD accounts
// are intentionally not included.
const TEAM = [
  { name: 'John Smith', department: 'IT Support', email: 'jsmith@zooland.local' },
  { name: 'Barbara Wilson', department: 'Human Resources', email: 'bwilson@zooland.local' },
  { name: 'Michelle Chen', department: 'Finance', email: 'mchen@zooland.local' },
  { name: 'Maria Lopez', department: 'Logistics', email: 'mlopez@zooland.local' },
  { name: 'Robert Thomas', department: 'Warehouse', email: 'rthomas@zooland.local' },
  { name: 'Alex Johnson', department: 'Marketing', email: 'ajohnson@zooland.local' },
  { name: 'Thomas Lee', department: 'Operations', email: 'tlee@zooland.local' },
  { name: 'Sarah Williams', department: 'Veterinary Services', email: 'swilliams@zooland.local' },
  { name: 'Patricia Garcia', department: 'Animal Care', email: 'pgarcia@zooland.local' },
  { name: 'Kevin Brown', department: 'Security', email: 'kbrown@zooland.local' },
  { name: 'Lisa Martinez', department: 'Facilities', email: 'lmartinez@zooland.local' },
  { name: 'David Jones', department: 'Research', email: 'djones@zooland.local' },
  { name: 'Nicole Anderson', department: 'Education', email: 'nanderson@zooland.local' },
  { name: 'Christopher Wilson', department: 'Retail', email: 'cwilson@zooland.local' },
  { name: 'Emma Miller', department: 'Administration', email: 'emiller@zooland.local' },
];

router.get('/', (req, res) => {
  res.json(TEAM);
});

module.exports = router;
