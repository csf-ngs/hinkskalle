<template>
  <v-expansion-panel v-if="manifest">
    <v-expansion-panel-header>
      <v-row no-gutters>
        <v-col>
          <span v-if="manifest.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip
              color="green lighten-1"
              v-for="tag in manifest.tags" :key="tag">
                {{tag}}
            </v-chip>
          </span>
        </v-col>
        <v-col>
          <template v-if="manifest.type=='singularity'">
            <v-icon>mdi-adjust</v-icon>
            Singularity
          </template>
          <template v-else-if="manifest.type=='docker'">
            <v-icon>mdi-ferry</v-icon>
            Docker
          </template>
          <template v-else-if="manifest.type=='oras'">
            <v-icon>mdi-folder</v-icon>
            ORAS
          </template>
          <template v-else-if="manifest.type=='other'">
            <v-icon>mdi-file-question</v-icon>
          </template>
          <template v-else-if="manifest.type=='invalid'">
            <v-icon color="error">mdi-file-cancel-outline</v-icon>
          </template>

        </v-col>
      </v-row>
    </v-expansion-panel-header>
  </v-expansion-panel>
</template>
<script lang="ts">
import { Manifest } from '@/store/models';
import Vue from 'vue';

export default Vue.extend({
  name: 'ManifestDetails',
  props: {
    manifest: {
      type: Manifest,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data: (): { localState: {} } => ({
    localState: {},
  }),
  computed: {},
  methods: {},
});
</script>