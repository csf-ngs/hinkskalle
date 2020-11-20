<template>
   <v-expansion-panel v-if="image">
    <v-expansion-panel-header>
      <v-row no-gutters>
        <v-col>
          <span v-if="image.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip color="light-green lighten-2" v-for="tag in image.tags" :key="tag" @click.stop="copyTag(tag)">{{tag}}</v-chip>
          </span>
        </v-col>
        <v-col class="d-flex align-center">
          <v-btn text icon @click.stop="inspect()">
            <v-icon large>mdi-file-code-outline</v-icon>
            <v-dialog v-model="localState.showDef">
              <v-card>
                <v-card-title class="headline green lighten-2">
                  Singularity Definition
                </v-card-title>
                <v-card-text>
                  <pre class="text--primary">{{localState.meta.deffile}}</pre>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" text @click="localState.showDef = false">
                    What a nice definition file!
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-btn>
          <v-badge :content="image.downloadCount || '0'" overlap color="blue-grey lighten-1">
            <v-icon large>mdi-download</v-icon>
          </v-badge>
        </v-col>
      </v-row>
    </v-expansion-panel-header> 
    <v-expansion-panel-content>
      <hsk-text-input v-for="tag in image.tags" :key="tag" :label="'Pull '+tag" :static-value="pullURL(tag)"></hsk-text-input>
      <v-row>
        <v-col>
          <hsk-text-input label="Created" :static-value="image.createdAt | moment('YYYY-MM-DD HH:mm:ss')"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Created By" :static-value="image.createdBy"></hsk-text-input>
        </v-col>
      </v-row>
      <hsk-text-input 
        label="Description" 
        field="description" 
        :obj="image" 
        action="images/update"
        @updated="image=$event"></hsk-text-input>
      <hsk-text-input label="Hash" :static-value="image.hash"></hsk-text-input>
      <hsk-text-input label="Size" :static-value="image.size | prettyBytes()"></hsk-text-input>
      <v-row>
        <v-col>
          <hsk-text-input type="yesno" label="Uploaded" :static-value="image.uploaded"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Downloads" :static-value="image.downloadCount"></hsk-text-input>
        </v-col>
      </v-row>
    </v-expansion-panel-content>
   </v-expansion-panel>
</template>
<script lang="ts">
import { InspectAttributes } from '@/store/models';
import Vue from 'vue';

interface State {
  meta: InspectAttributes;
  showDef: boolean;
}

export default Vue.extend({
  name: 'ImageDetails',
  props: [ 'image' ],
  data: (): { localState: State } => ({
    localState: {
      meta: {
        deffile: '',
      },
      showDef: false,
    },
  }),
  methods: {
    pullURL(tag: string): string {
      return `library://${this.image.entityName}/${this.image.collectionName}/${this.image.containerName}:${tag}`
    },
    copyTag(tag: string) {
      this.$copyText(this.pullURL(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard."));
    },
    inspect() {
      this.$store.dispatch('images/inspect', this.image)
        .then(response => {
          console.log(response);
          this.localState.meta = response;
          this.localState.showDef = true;
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
  }
});
</script>